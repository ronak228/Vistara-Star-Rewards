# app.py - Vistara Rewards
# Dual CSV system:
#   CSV 1 — Orders CSV  → verifies Order ID is real (not fake/random)
#   CSV 2 — Returns CSV → rejects returned/RTO orders
# Auto-approves after 15 days if: verified in Orders CSV + NOT in Returns CSV

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, random, string, hashlib, logging, tempfile, csv, io
from datetime import datetime, timezone
import re
import psycopg
from psycopg.rows import dict_row
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    elif request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
    return response

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger("vistara")

# ── CONFIG ────────────────────────────────────────────────────────────
DATABASE_URL   = os.getenv("DATABASE_URL")
DB_SSLMODE     = os.getenv("DB_SSLMODE", "require")
ADMIN_SECRET   = os.getenv("ADMIN_SECRET", "")
MAX_FILE_BYTES = int(os.getenv("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))
ALLOWED_EXTS   = {"png", "jpg", "jpeg", "gif", "webp"}
RATE_WIN_MIN   = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "60"))
RATE_MAX_REQ   = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "5"))

MEESHO_ORDER_ID_REGEX = re.compile(r'^\d{15,19}_\d{1,2}$')

R2_ON         = os.getenv("R2_ENABLED", "false").lower() == "true"
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY", "")
R2_BUCKET     = os.getenv("R2_BUCKET_NAME", "vistara-screenshots")

UPLOAD_DIR = os.getenv("UPLOAD_FOLDER", "/tmp/vistara_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES

# ── CSV COLUMN NAMES ──────────────────────────────────────────────────
# Orders CSV (all Meesho orders — to verify real IDs)
# Meesho Orders CSV uses "Sub Order No"; Returns CSV uses "Suborder Number"
ORDERS_CSV_SUBORDER_COL = os.getenv("ORDERS_CSV_SUBORDER_COL", "Sub Order No")

# Returns CSV (returned/RTO orders only)
RETURN_CSV_SUBORDER_COL = os.getenv("RETURN_CSV_SUBORDER_COL", "Suborder Number")
RETURN_CSV_TYPE_COL     = os.getenv("RETURN_CSV_TYPE_COL",     "Type of Return")

RETURN_TYPE_VALUES = {
    "customer return", "courier return (rto)", "courier return",
    "rto", "return", "rto delivered",
}


# ── HELPERS ───────────────────────────────────────────────────────────
def mask(email):
    if not email or "@" not in email: return ""
    n, d = email.split("@", 1)
    return (n[:2] + "*" * max(1, len(n)-2) if len(n) > 2 else n[:1]+"*") + "@" + d

def client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() if fwd else (request.remote_addr or "unknown")

def ua_hash():
    return hashlib.sha256(request.headers.get("User-Agent","").encode()).hexdigest()[:32]

def ok_ext(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTS

def gen_token():
    return "VST-" + "".join(random.choices(string.digits, k=4))

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def wrap(*a, **kw):
        if not ADMIN_SECRET or request.headers.get("X-Admin-Secret","") != ADMIN_SECRET:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*a, **kw)
    return wrap


# ── DATABASE ──────────────────────────────────────────────────────────
_pool = None

def init_pool():
    global _pool
    if not DATABASE_URL: return
    try:
        from psycopg_pool import ConnectionPool
        _pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=5, open=True,
            kwargs={"sslmode": DB_SSLMODE, "connect_timeout": 15, "row_factory": dict_row})
        log.info("DB pool initialised")
    except Exception as e:
        log.warning("Pool init failed: %s", e)
        _pool = None

with app.app_context():
    init_pool()

def get_db(retries=3):
    global _pool
    import time
    if _pool is not None:
        try: return _pool.getconn(timeout=10)
        except Exception as e: log.warning("Pool getconn failed: %s", e)
    if not DATABASE_URL: return None
    for attempt in range(retries):
        try:
            return psycopg.connect(DATABASE_URL, sslmode=DB_SSLMODE,
                connect_timeout=15, autocommit=False, row_factory=dict_row)
        except Exception as e:
            log.warning("DB attempt %d failed: %s", attempt+1, e)
            if attempt < retries - 1: time.sleep(2)
    return None

def release_db(conn):
    """Return connection to pool if pooled, otherwise close it directly."""
    global _pool
    if conn is None:
        return
    if _pool is not None:
        try:
            _pool.putconn(conn)
            return
        except Exception as e:
            log.warning("Pool putconn failed: %s", e)
    try:
        release_db(conn)
    except Exception:
        pass

def get_config(conn) -> dict:
    try:
        with conn.cursor() as c:
            c.execute("SELECT key, value FROM system_config")
            return {r["key"]: r["value"] for r in c.fetchall()}
    except Exception: return {}

def audit(cur, order_id, from_s, to_s, reason, sync_id=None):
    try:
        cur.execute("""INSERT INTO order_status_log(order_id,from_status,to_status,reason,csv_sync_log_id)
            VALUES(%s,%s,%s,%s,%s)""", (order_id, from_s, to_s, reason, sync_id))
    except Exception as e:
        log.warning("audit log failed: %s", e)


# ── FILE STORAGE ──────────────────────────────────────────────────────
def save_file(file_obj, filename: str) -> str:
    if R2_ON and R2_ACCOUNT_ID:
        try:
            import boto3
            from botocore.config import Config
            s3 = boto3.client("s3",
                endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY,
                config=Config(signature_version="s3v4"), region_name="auto")
            file_obj.seek(0)
            s3.upload_fileobj(file_obj, R2_BUCKET, filename)
            return f"r2://{R2_BUCKET}/{filename}"
        except Exception as e:
            log.error("R2 upload failed: %s", e)
    path = os.path.join(UPLOAD_DIR, filename)
    file_obj.seek(0)
    file_obj.save(path)
    return path


# ── RATE LIMITING ─────────────────────────────────────────────────────
def check_rate(conn, identifier, id_type) -> bool:
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO rate_limits(identifier,identifier_type,window_start,request_count)
                VALUES(%s,%s,NOW(),1)
                ON CONFLICT(identifier,identifier_type) DO UPDATE SET
                  request_count = CASE
                    WHEN NOW()-rate_limits.window_start > (%s||' minutes')::INTERVAL THEN 1
                    ELSE rate_limits.request_count+1 END,
                  window_start = CASE
                    WHEN NOW()-rate_limits.window_start > (%s||' minutes')::INTERVAL THEN NOW()
                    ELSE rate_limits.window_start END
                RETURNING request_count""", (identifier, id_type, RATE_WIN_MIN, RATE_WIN_MIN))
            row = c.fetchone()
            return (row["request_count"] if row else 1) <= RATE_MAX_REQ
    except Exception as e:
        log.warning("rate check fail-open: %s", e)
        return True


# ── CSV PARSERS ───────────────────────────────────────────────────────
def _find_header_and_parse(filepath: str, target_col: str):
    """Skip Meesho metadata rows, find real header, return (rows, fieldnames).
    Handles column name variations (e.g., 'Sub Order No' vs 'Suborder Number')"""
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        lines = f.readlines()
    
    header_idx = None
    reader_obj = None
    
    # Try exact match first
    for i, line in enumerate(lines):
        if target_col in line:
            header_idx = i
            break
    
    # If exact match not found, try fuzzy matching for common variations
    if header_idx is None:
        target_norm = target_col.lower().replace(" ", "").replace("_", "")
        for i, line in enumerate(lines):
            line_norm = line.lower().replace(" ", "").replace("_", "")
            if target_norm in line_norm:
                header_idx = i
                break
    
    if header_idx is None:
        log.warning("Header '%s' not found in CSV", target_col)
        return [], []
    
    content = "".join(lines[header_idx:])
    reader_obj = csv.DictReader(io.StringIO(content))
    rows = list(reader_obj)
    
    # Find the actual column name in the CSV
    actual_col_name = None
    if reader_obj.fieldnames:
        target_norm = target_col.lower().replace(" ", "").replace("_", "")
        for fname in reader_obj.fieldnames:
            fname_norm = fname.lower().replace(" ", "").replace("_", "")
            if target_norm in fname_norm or fname_norm in target_norm:
                actual_col_name = fname
                break
        if not actual_col_name:
            actual_col_name = reader_obj.fieldnames[0] if reader_obj.fieldnames else None
    
    return rows, reader_obj.fieldnames, actual_col_name


def parse_orders_csv(filepath: str) -> set:
    """
    Parse Meesho Orders CSV (all orders download).
    Returns set of valid Suborder Numbers — these are REAL Meesho order IDs.
    """
    valid_ids = set()
    try:
        rows, fieldnames, actual_col = _find_header_and_parse(filepath, ORDERS_CSV_SUBORDER_COL)
        if not actual_col:
            log.error("Orders CSV missing '%s'. Got: %s", ORDERS_CSV_SUBORDER_COL, fieldnames)
            return valid_ids
        for row in rows:
            sid = str(row.get(actual_col, "")).strip()
            if sid:
                valid_ids.add(sid)
        log.info("Orders CSV parsed: %d valid order IDs found (column: %s)", len(valid_ids), actual_col)
    except Exception as e:
        log.error("parse_orders_csv error: %s", e)
    return valid_ids


def parse_return_csv(filepath: str) -> set:
    """
    Parse Meesho Returns CSV (returns/RTO download).
    Returns set of Suborder Numbers that are returned.
    """
    returned_ids = set()
    try:
        rows, fieldnames, actual_col = _find_header_and_parse(filepath, RETURN_CSV_SUBORDER_COL)
        if not actual_col:
            log.error("Returns CSV missing '%s'. Got: %s", RETURN_CSV_SUBORDER_COL, fieldnames)
            return returned_ids

        # Find actual type column name in CSV (fuzzy match)
        actual_type_col = None
        if fieldnames:
            type_norm = RETURN_CSV_TYPE_COL.lower().replace(" ", "").replace("_", "")
            for fname in fieldnames:
                fname_norm = fname.lower().replace(" ", "").replace("_", "")
                if type_norm in fname_norm or fname_norm in type_norm:
                    actual_type_col = fname
                    break

        for row in rows:
            sid = str(row.get(actual_col, "")).strip()
            ret_type = str(row.get(actual_type_col or RETURN_CSV_TYPE_COL, "")).strip().lower()
            # Only include rows that are explicitly a return/RTO type
            if sid and (ret_type in RETURN_TYPE_VALUES):
                returned_ids.add(sid)
        log.info("Returns CSV parsed: %d returned IDs found", len(returned_ids))
    except Exception as e:
        log.error("parse_return_csv error: %s", e)
    return returned_ids


# ── AUTO APPROVE ──────────────────────────────────────────────────────
def auto_approve_eligible(conn, sync_id: int) -> dict:
    """
    Auto-approve orders that meet ALL conditions:
    1. status = 'under_review' (was verified in Orders CSV)
    2. ever_showed_return = FALSE (never in Returns CSV)
    3. verified_in_orders_csv = TRUE (confirmed real Meesho order)
    4. 15+ days passed since submission
    """
    cfg   = get_config(conn)
    cool  = int(cfg.get("cooling_days", "15"))
    auto  = cfg.get("auto_approve_enabled", "true").lower() == "true"
    stats = dict(approved=0, checked=0)
    if not auto: return stats

    now = datetime.now(timezone.utc)
    with conn.cursor() as c:
        c.execute("""SELECT order_id, email, token, submitted_at
                     FROM orders
                     WHERE status = 'under_review'
                       AND ever_showed_return = FALSE
                       AND verified_in_orders_csv = TRUE""")
        candidates = c.fetchall()

    for o in candidates:
        stats["checked"] += 1
        ref = o.get("submitted_at")
        if not ref: continue
        if (now - ref).days < cool: continue
        with conn.cursor() as c:
            c.execute("""UPDATE orders SET status='approved', approved_at=NOW(), updated_at=NOW()
                WHERE order_id=%s AND status='under_review' RETURNING order_id""", (o["order_id"],))
            if c.fetchone():
                audit(c, o["order_id"], "under_review", "approved",
                      f"auto_approve:day={( now - ref).days}>=cool={cool}", sync_id)
                stats["approved"] += 1
                log.info("APPROVED order_id=%s days=%d", o["order_id"], (now-ref).days)
        conn.commit()

    return stats


def reject_unverified_stale(conn, sync_id: int) -> dict:
    """
    Reject orders that were NEVER verified in any Orders CSV after 20 days.
    These are likely fake/random IDs — real orders always appear in Meesho CSV within days.
    """
    cfg   = get_config(conn)
    stale = int(cfg.get("stale_order_days", "20"))
    stats = dict(rejected=0)
    now   = datetime.now(timezone.utc)

    with conn.cursor() as c:
        c.execute("""SELECT order_id, submitted_at FROM orders
                     WHERE status = 'pending'
                       AND verified_in_orders_csv = FALSE
                       AND submitted_at < NOW() - (%s || ' days')::INTERVAL""", (str(stale),))
        candidates = c.fetchall()

    for o in candidates:
        with conn.cursor() as c:
            c.execute("""UPDATE orders SET status='rejected', rejected_at=NOW(),
                rejection_reason='Order ID not found in any Meesho Orders CSV after 20 days — likely invalid or fake ID',
                updated_at=NOW()
              WHERE order_id=%s AND status='pending' RETURNING order_id""", (o["order_id"],))
            if c.fetchone():
                audit(c, o["order_id"], "pending", "rejected",
                      "never_verified_in_orders_csv:stale", sync_id)
                stats["rejected"] += 1
                log.info("STALE-REJECTED fake/unverified order_id=%s", o["order_id"])
        conn.commit()

    return stats


# ── PAGES ─────────────────────────────────────────────────────────────
@app.route("/")
def index():       return render_template("index.html")

@app.route("/check-stars")
def check_stars(): return render_template("check-stars.html")

@app.route("/admin")
def admin():       return render_template("admin.html")


# ── API: SUBMIT ORDER ─────────────────────────────────────────────────
@app.route("/api/submit", methods=["POST"])
def submit():
    ip = client_ip()
    uh = ua_hash()

    content_len = request.content_length or 0
    if content_len > MAX_FILE_BYTES:
        return jsonify({"success": False, "error": "Request too large. Max 5MB allowed."}), 413

    name     = (request.form.get("name",     "") or "").strip()
    email    = (request.form.get("email",    "") or "").strip().lower()
    order_id = (request.form.get("order_id", "") or "").strip()

    if not name or not email or not order_id:
        return jsonify({"success": False, "error": "All fields are required."}), 400
    if len(name) < 2 or len(name) > 100:
        return jsonify({"success": False, "error": "Name must be 2–100 characters."}), 400
    if not re.match(r'^[ऀ-ॿ਀-੿଀-୿a-zA-Z\s.\'-]+$', name):
        return jsonify({"success": False, "error": "Name contains invalid characters."}), 400
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email) or len(email) > 254:
        return jsonify({"success": False, "error": "Invalid email address."}), 400
    if not MEESHO_ORDER_ID_REGEX.match(order_id):
        return jsonify({"success": False,
            "error": "Invalid Order ID format. Meesho Order IDs look like: 265437129718567616_1"}), 400

    of = request.files.get("order_screenshot")
    if not of or not of.filename:
        return jsonify({"success": False, "error": "Order screenshot is required."}), 400
    if not ok_ext(of.filename):
        return jsonify({"success": False, "error": "Screenshot must be PNG, JPG, GIF or WEBP."}), 400
    file_bytes = of.read()
    if len(file_bytes) == 0 or len(file_bytes) > MAX_FILE_BYTES:
        return jsonify({"success": False, "error": "Screenshot must be between 1 byte and 5MB."}), 400
    MAGIC = {b'\xff\xd8\xff': "jpg", b'\x89PNG': "png", b'GIF8': "gif", b'RIFF': "webp"}
    if not any(file_bytes[:len(sig)] == sig for sig in MAGIC):
        return jsonify({"success": False, "error": "File does not appear to be a valid image."}), 400
    of.seek(0)

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable. Try again shortly."}), 500

    try:
        with conn.cursor() as c:
            # Blocked IP?
            c.execute("SELECT 1 FROM blocked_entities WHERE entity_type='ip' AND value=%s LIMIT 1", (ip,))
            if c.fetchone():
                return jsonify({"success": False, "error": "Access denied."}), 403

            # Blocked email?
            c.execute("SELECT 1 FROM blocked_entities WHERE entity_type='email' AND lower(value)=lower(%s) LIMIT 1", (email,))
            if c.fetchone():
                return jsonify({"success": False, "error": "This email has been restricted. Contact support."}), 403

            # Rate limits
            if not check_rate(conn, ip, "ip"):
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False, "error": "Too many submissions from your device. Wait an hour."}), 429
            if not check_rate(conn, email, "email"):
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False, "error": "Too many submissions from this email. Wait an hour."}), 429

            # Daily cap
            c.execute("""SELECT COUNT(*) as cnt FROM orders WHERE lower(email)=lower(%s)
                AND submitted_at > NOW() - INTERVAL '24 hours'""", (email,))
            if (c.fetchone() or {}).get("cnt", 0) >= 3:
                return jsonify({"success": False, "error": "Maximum 3 orders per day from one email."}), 429

            # ── CHECK 1: Already in Returns blocklist? → Reject instantly ──
            c.execute("SELECT 1 FROM returns_blocklist WHERE suborder_id=%s LIMIT 1", (order_id,))
            if c.fetchone():
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False,
                    "error": "This order was returned/cancelled and is not eligible for stars."}), 409

            # ── CHECK 2: Duplicate order ID? ──
            c.execute("SELECT status FROM orders WHERE lower(order_id)=lower(%s) LIMIT 1", (order_id,))
            if c.fetchone():
                _log_attempt(conn, ip, email, order_id, was_duplicate=True)
                return jsonify({"success": False,
                    "error": "This Order ID has already been submitted. Each order earns stars only once."}), 409

            # Fraud scoring
            c.execute("""SELECT COUNT(DISTINCT lower(email)) as cnt FROM orders
                WHERE ip_address=%s AND submitted_at > NOW() - INTERVAL '24 hours'""", (ip,))
            ip_email_count = (c.fetchone() or {}).get("cnt", 0)
            c.execute("""SELECT COUNT(*) as cnt FROM orders WHERE lower(email)=lower(%s)
                AND submitted_at > NOW() - INTERVAL '7 days'""", (email,))
            week_count = (c.fetchone() or {}).get("cnt", 0)
            c.execute("""SELECT COUNT(*) as cnt FROM submission_attempts
                WHERE ip_address=%s AND attempted_at > NOW() - INTERVAL '1 hour'
                AND (was_duplicate OR was_invalid_fmt OR blocked)""", (ip,))
            bad_attempts = (c.fetchone() or {}).get("cnt", 0)

            fraud_score   = 0
            fraud_reasons = []
            if ip_email_count >= 3:  fraud_score += 30; fraud_reasons.append(f"ip_multi_email:{ip_email_count}")
            if week_count >= 5:      fraud_score += 20; fraud_reasons.append(f"high_weekly:{week_count}")
            if bad_attempts >= 5:    fraud_score += 25; fraud_reasons.append(f"bad_attempts:{bad_attempts}")

            if fraud_score >= 80:
                try:
                    c.execute("""INSERT INTO blocked_entities(entity_type,value,reason)
                        VALUES('ip',%s,%s) ON CONFLICT(entity_type,value) DO NOTHING""",
                        (ip, f"Auto-blocked fraud_score={fraud_score}"))
                    conn.commit()
                except Exception: pass
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False, "error": "Suspicious activity detected."}), 403

        # Save files
        pfx = random.randint(10000, 99999)
        op  = save_file(of, f"{pfx}_{secure_filename(of.filename)}")
        rp  = None
        rf  = request.files.get("rating_screenshot")
        if rf and rf.filename and ok_ext(rf.filename):
            rb = rf.read()
            if 0 < len(rb) <= MAX_FILE_BYTES:
                rf.seek(0)
                rp = save_file(rf, f"{pfx}r_{secure_filename(rf.filename)}")

        with conn.cursor() as c:
            c.execute("""INSERT INTO users(email) VALUES(%s)
                ON CONFLICT(email) DO UPDATE SET updated_at=NOW()
                RETURNING total_stars""", (email,))
            stars = (c.fetchone() or {}).get("total_stars", 0)

        token = None
        for _ in range(10):
            t = gen_token()
            try:
                with conn.cursor() as c:
                    c.execute("""INSERT INTO orders(
                        order_id,email,name,token,status,
                        screenshot_order_path,screenshot_rating_path,
                        ip_address,user_agent_hash,submitted_at,
                        fraud_score,fraud_reasons,submission_count_snapshot,
                        verified_in_orders_csv)
                      VALUES(%s,%s,%s,%s,'pending',%s,%s,%s,%s,NOW(),%s,%s,%s,FALSE)""",
                        (order_id, email, name, t, op, rp, ip, uh,
                         fraud_score, ",".join(fraud_reasons) or None, week_count))
                token = t; break
            except Exception as e:
                if "unique" in str(e).lower(): conn.rollback(); continue
                raise

        if not token:
            conn.rollback()
            return jsonify({"success": False, "error": "Token error — please retry."}), 500

        _log_attempt(conn, ip, email, order_id)
        conn.commit()
        log.info("submit_ok email=%s order_id=%s", mask(email), order_id)
        return jsonify({"success": True, "token": token, "total_stars": stars,
            "message": "Order submitted! Stars added after verification (up to 15 days)."}), 200

    except Exception as e:
        try: conn.rollback()
        except Exception: pass
        log.error("submit_db: %s", e)
        return jsonify({"success": False, "error": "Server error. Please try again."}), 500
    finally:
        try: release_db(conn)
        except Exception: pass


def _log_attempt(conn, ip, email, order_id,
                 was_duplicate=False, was_invalid_fmt=False, blocked=False):
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO submission_attempts
                (ip_address,email,order_id,was_duplicate,was_invalid_fmt,blocked)
                VALUES(%s,%s,%s,%s,%s,%s)""",
                (ip, email, order_id, was_duplicate, was_invalid_fmt, blocked))
        conn.commit()
    except Exception as ex:
        log.warning("log_attempt_error: %s", ex)


# ── ADMIN: UPLOAD ORDERS CSV ──────────────────────────────────────────
@app.route("/api/admin/upload-orders-csv", methods=["POST"])
@require_admin
def upload_orders_csv():
    """
    CSV 1 — All Meesho Orders CSV.
    Purpose: Verify submitted Order IDs are REAL Meesho orders (not random/fake).
    Logic:
      - Extract all Suborder Numbers from CSV → store in orders_whitelist
      - Mark matching pending orders as verified + move to under_review
      - Reject orders that are REAL but found in returns_blocklist (extra safety)
      - Run auto-approve for verified orders past 15 days cooling
    """
    if "csv_file" not in request.files:
        return jsonify({"success": False, "error": "csv_file required"}), 400
    f = request.files["csv_file"]
    if not f.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "error": "Must be a .csv file"}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        f.save(tmp.name); tmp_path = tmp.name

    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO csv_sync_log(filename, synced_by)
                VALUES(%s,'orders_csv_upload') RETURNING id""", (f.filename,))
            sid = c.fetchone()["id"]
        conn.commit()

        # Step 1: Parse — get all valid suborder IDs from this CSV
        valid_ids = parse_orders_csv(tmp_path)
        if not valid_ids:
            return jsonify({"success": False,
                "error": f"No order IDs found. Expected column '{ORDERS_CSV_SUBORDER_COL}' (or similar). Upload the Meesho 'All Orders' CSV, not the Returns CSV."}), 400

        # Step 2: Store ALL valid IDs in orders_whitelist
        with conn.cursor() as c:
            for vid in valid_ids:
                c.execute("""INSERT INTO orders_whitelist(suborder_id, source_filename, added_at)
                    VALUES(%s,%s,NOW())
                    ON CONFLICT(suborder_id) DO UPDATE SET
                      source_filename=EXCLUDED.source_filename, added_at=NOW()""",
                    (vid, f.filename))
        conn.commit()
        log.info("Stored %d IDs in orders_whitelist", len(valid_ids))

        # Step 3: Process each submitted order against whitelist
        stats = dict(
            total_ids_in_csv=len(valid_ids),
            rows_verified=0,      # pending → under_review (real order confirmed)
            rows_rejected=0,      # in orders CSV but ALSO in returns = reject
            rows_skipped=0,       # not in our DB (customer never submitted)
            auto_approved=0,
            auto_approve_checked=0,
        )

        with conn.cursor() as c:
            c.execute("""SELECT order_id, status, email FROM orders
                WHERE verified_in_orders_csv=FALSE
                  AND status IN ('pending','under_review')""")
            unverified = c.fetchall()

        for order in unverified:
            oid = order["order_id"]
            if oid not in valid_ids:
                stats["rows_skipped"] += 1
                continue

            # This order IS in the Orders CSV → it's a real Meesho order
            # But also check: is it in returns_blocklist? (extra safety)
            with conn.cursor() as c:
                c.execute("SELECT 1 FROM returns_blocklist WHERE suborder_id=%s", (oid,))
                in_returns = c.fetchone()

            if in_returns:
                # Real order but already returned — reject
                with conn.cursor() as c:
                    c.execute("""UPDATE orders SET status='rejected', rejected_at=NOW(),
                        ever_showed_return=TRUE,
                        rejection_reason='Order confirmed in Meesho records but was returned/RTO — not eligible for stars',
                        updated_at=NOW()
                      WHERE order_id=%s AND status NOT IN ('rejected','disputed')
                      RETURNING order_id""", (oid,))
                    if c.fetchone():
                        audit(c, oid, order["status"], "rejected",
                              "orders_csv:verified_but_in_returns_blocklist", sid)
                        stats["rows_rejected"] += 1
                conn.commit()
                continue

            # Real order, not returned → verify and move to under_review
            with conn.cursor() as c:
                c.execute("""UPDATE orders SET
                    verified_in_orders_csv=TRUE,
                    orders_csv_verified_at=NOW(),
                    orders_csv_filename=%s,
                    status=CASE WHEN status='pending' THEN 'under_review' ELSE status END,
                    review_started_at=CASE WHEN status='pending' THEN NOW() ELSE review_started_at END,
                    updated_at=NOW()
                  WHERE order_id=%s AND status IN ('pending','under_review')
                  RETURNING order_id, status""", (f.filename, oid))
                updated = c.fetchone()
                if updated:
                    audit(c, oid, order["status"], "under_review",
                          "orders_csv:verified_real_meesho_order", sid)
                    stats["rows_verified"] += 1
            conn.commit()

        # Step 4: Also reject fake stale orders (unverified after 20 days)
        stale_stats = reject_unverified_stale(conn, sid)
        stats["stale_rejected"] = stale_stats["rejected"]

        # Step 5: Auto-approve eligible orders (verified + 15 days + not returned)
        approve_stats = auto_approve_eligible(conn, sid)
        stats["auto_approved"]        = approve_stats["approved"]
        stats["auto_approve_checked"] = approve_stats["checked"]

        # Update sync log
        with conn.cursor() as c:
            c.execute("""UPDATE csv_sync_log SET
                rows_processed=%s, rows_matched=%s, rows_approved=%s, rows_skipped=%s
              WHERE id=%s""",
                (stats["total_ids_in_csv"], stats["rows_verified"],
                 stats["auto_approved"], stats["rows_skipped"], sid))
        conn.commit()

        return jsonify({
            "success": True, "stats": stats, "sync_log_id": sid,
            "message": (
                f"✅ Orders CSV processed: "
                f"{stats['total_ids_in_csv']} real order IDs found, "
                f"{stats['rows_verified']} verified & moved to review, "
                f"{stats['rows_rejected']} rejected (returned), "
                f"{stats.get('stale_rejected',0)} fake/stale IDs rejected, "
                f"{stats['auto_approved']} auto-approved."
            )
        }), 200

    except Exception as e:
        conn.rollback()
        log.error("upload_orders_csv: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        release_db(conn)
        try: os.unlink(tmp_path)
        except Exception: pass


# ── ADMIN: UPLOAD RETURNS CSV ─────────────────────────────────────────
@app.route("/api/admin/upload-returns-csv", methods=["POST"])
@require_admin
def upload_returns_csv():
    """
    CSV 2 — Meesho Returns CSV (RTO + Customer Returns only).
    Purpose: Instantly reject any submitted orders that were returned.
    Logic:
      - Extract all returned Suborder Numbers
      - Store in returns_blocklist permanently
      - Reject/dispute any matching orders in DB
      - Run auto-approve for clean verified orders past 15 days
    """
    if "csv_file" not in request.files:
        return jsonify({"success": False, "error": "csv_file required"}), 400
    f = request.files["csv_file"]
    if not f.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "error": "Must be a .csv file"}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        f.save(tmp.name); tmp_path = tmp.name

    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO csv_sync_log(filename, synced_by)
                VALUES(%s,'returns_csv_upload') RETURNING id""", (f.filename,))
            sid = c.fetchone()["id"]
        conn.commit()

        returned_ids = parse_return_csv(tmp_path)
        if not returned_ids:
            return jsonify({"success": False,
                "error": f"No returned/RTO order IDs found. Expected column '{RETURN_CSV_SUBORDER_COL}' with return types like 'Customer Return' or 'Courier Return (RTO)'. Upload the Meesho 'Completed & Delivered' Returns CSV."}), 400

        # Store ALL returned IDs in returns_blocklist permanently
        with conn.cursor() as c:
            for rid in returned_ids:
                c.execute("""INSERT INTO returns_blocklist(suborder_id,source_filename,added_at)
                    VALUES(%s,%s,NOW())
                    ON CONFLICT(suborder_id) DO UPDATE SET
                      source_filename=EXCLUDED.source_filename, added_at=NOW()""",
                    (rid, f.filename))
        conn.commit()

        stats = dict(
            returned_ids_in_csv=len(returned_ids),
            rows_matched=0,
            rows_rejected=0,
            rows_disputed=0,
            rows_skipped=0,
            auto_approved=0,
            auto_approve_checked=0,
        )

        for rid in returned_ids:
            with conn.cursor() as c:
                c.execute("SELECT order_id, status FROM orders WHERE order_id=%s", (rid,))
                order = c.fetchone()

            if not order:
                stats["rows_skipped"] += 1
                continue

            stats["rows_matched"] += 1
            cur_status = order["status"]

            with conn.cursor() as c:
                # Permanently mark ever_showed_return
                c.execute("""UPDATE orders SET ever_showed_return=TRUE,
                    consecutive_delivered_count=0,
                    csv_last_status='returned_via_returns_csv',
                    csv_last_seen_at=NOW(), updated_at=NOW()
                  WHERE order_id=%s""", (rid,))

                if cur_status == "approved":
                    # Late return — already gave star
                    c.execute("""UPDATE orders SET status='disputed',
                        admin_note=COALESCE(admin_note||' | ','')||
                                  'LATE RETURN via Returns CSV '||NOW()::DATE::TEXT,
                        updated_at=NOW() WHERE order_id=%s""", (rid,))
                    audit(c, rid, "approved", "disputed",
                          "late_return:returns_csv_upload", sid)
                    stats["rows_disputed"] += 1
                    log.warning("DISPUTED late return order_id=%s", rid)

                elif cur_status not in ("rejected", "disputed", "stale"):
                    c.execute("""UPDATE orders SET status='rejected', rejected_at=NOW(),
                        rejection_reason='Order was returned or RTO — found in Meesho Returns CSV. Returned orders are not eligible for reward stars.',
                        updated_at=NOW()
                      WHERE order_id=%s AND status NOT IN ('rejected','disputed')""", (rid,))
                    audit(c, rid, cur_status, "rejected",
                          "returns_csv:order_returned_or_rto", sid)
                    stats["rows_rejected"] += 1
                    log.info("REJECTED returned order_id=%s", rid)

            conn.commit()

        # Also reject stale unverified orders
        stale_stats = reject_unverified_stale(conn, sid)
        stats["stale_rejected"] = stale_stats["rejected"]

        # Auto-approve clean eligible orders
        approve_stats = auto_approve_eligible(conn, sid)
        stats["auto_approved"]        = approve_stats["approved"]
        stats["auto_approve_checked"] = approve_stats["checked"]

        with conn.cursor() as c:
            c.execute("""UPDATE csv_sync_log SET
                rows_processed=%s, rows_matched=%s,
                rows_returned=%s, rows_approved=%s,
                rows_disputed=%s, rows_skipped=%s
              WHERE id=%s""",
                (stats["returned_ids_in_csv"], stats["rows_matched"],
                 stats["rows_rejected"], stats["auto_approved"],
                 stats["rows_disputed"], stats["rows_skipped"], sid))
        conn.commit()

        return jsonify({
            "success": True, "stats": stats, "sync_log_id": sid,
            "message": (
                f"✅ Returns CSV processed: "
                f"{stats['returned_ids_in_csv']} returned IDs found, "
                f"{stats['rows_matched']} matched in DB, "
                f"{stats['rows_rejected']} rejected, "
                f"{stats['rows_disputed']} disputed, "
                f"{stats['auto_approved']} auto-approved."
            )
        }), 200

    except Exception as e:
        conn.rollback()
        log.error("upload_returns_csv: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        release_db(conn)
        try: os.unlink(tmp_path)
        except Exception: pass


# ── ADMIN: RUN APPROVALS (GitHub Actions daily 3AM IST) ───────────────
@app.route("/api/admin/run-approvals", methods=["POST"])
@require_admin
def run_approvals():
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO csv_sync_log(filename,synced_by)
                VALUES('github_actions_daily','github_actions') RETURNING id""")
            sid = c.fetchone()["id"]
        conn.commit()

        # Auto-approve eligible verified clean orders
        approve_stats = auto_approve_eligible(conn, sid)
        # Reject fake stale orders
        stale_stats = reject_unverified_stale(conn, sid)

        return jsonify({
            "success": True,
            "approved_count": approve_stats["approved"],
            "checked_count":  approve_stats["checked"],
            "stale_rejected": stale_stats["rejected"],
            "message": f"Daily: {approve_stats['approved']} approved, {stale_stats['rejected']} fake/stale rejected"
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        release_db(conn)


# ── ADMIN: MARK STALE ─────────────────────────────────────────────────
@app.route("/api/admin/mark-stale", methods=["POST"])
@require_admin
def mark_stale():
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO csv_sync_log(filename,synced_by)
                VALUES('mark_stale_manual','admin') RETURNING id""")
            sid = c.fetchone()["id"]
        conn.commit()
        stats = reject_unverified_stale(conn, sid)
        return jsonify({"success": True, "marked_count": stats["rejected"]}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        release_db(conn)


# ── ADMIN: PING ────────────────────────────────────────────────────────
@app.route("/api/admin/ping", methods=["POST"])
@require_admin
def admin_ping():
    conn = get_db(); counts = {}
    if conn:
        try:
            with conn.cursor() as c:
                c.execute("""SELECT
                    COUNT(*) FILTER(WHERE status='pending')      AS pending,
                    COUNT(*) FILTER(WHERE status='under_review') AS under_review,
                    COUNT(*) FILTER(WHERE status='approved')     AS approved,
                    COUNT(*) FILTER(WHERE status='rejected')     AS rejected,
                    COUNT(*) FILTER(WHERE status='disputed')     AS disputed,
                    COUNT(*) FILTER(WHERE status='stale')        AS stale,
                    COUNT(*) FILTER(WHERE verified_in_orders_csv=FALSE AND status='pending') AS unverified_pending
                  FROM orders""")
                counts = dict(c.fetchone() or {})
        except Exception: pass
        finally: release_db(conn)
    return jsonify({"success": True, "counts": counts}), 200


# ── ADMIN: ORDERS ──────────────────────────────────────────────────────
@app.route("/api/admin/orders", methods=["GET"])
@require_admin
def admin_orders():
    sf  = request.args.get("status")
    lim = min(int(request.args.get("limit", 100)), 500)
    off = int(request.args.get("offset", 0))
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            if sf:
                c.execute("SELECT * FROM v_admin_orders WHERE status=%s::order_status LIMIT %s OFFSET %s", (sf,lim,off))
            else:
                c.execute("SELECT * FROM v_admin_orders LIMIT %s OFFSET %s", (lim,off))
            rows = c.fetchall()
            c.execute("""SELECT
                COUNT(*) FILTER(WHERE status='pending')      AS pending,
                COUNT(*) FILTER(WHERE status='under_review') AS under_review,
                COUNT(*) FILTER(WHERE status='approved')     AS approved,
                COUNT(*) FILTER(WHERE status='rejected')     AS rejected,
                COUNT(*) FILTER(WHERE status='disputed')     AS disputed,
                COUNT(*) FILTER(WHERE status='stale')        AS stale
              FROM orders""")
            counts = c.fetchone()
        return jsonify({"success": True,
            "orders": [dict(r) for r in rows],
            "counts": dict(counts) if counts else {}}), 200
    finally: release_db(conn)


# ── ADMIN: UPDATE ORDER ────────────────────────────────────────────────
@app.route("/api/admin/update-order", methods=["POST"])
@require_admin
def update_order():
    d   = request.get_json(silent=True) or {}
    oid = d.get("order_id","").strip()
    ns  = d.get("status","").strip()
    rr  = d.get("rejection_reason","").strip()
    an  = d.get("admin_note","").strip()
    VALID = {"pending","under_review","approved","rejected","disputed"}
    if not oid or ns not in VALID:
        return jsonify({"success": False, "error": "Invalid params"}), 400
    if ns == "rejected" and not rr:
        return jsonify({"success": False, "error": "rejection_reason required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("SELECT status FROM orders WHERE order_id=%s", (oid,))
            cur = c.fetchone()
            if not cur: return jsonify({"success": False, "error": "Not found"}), 404
            c.execute("""UPDATE orders SET status=%s::order_status,
                rejection_reason=COALESCE(NULLIF(%s,''),rejection_reason),
                admin_note=COALESCE(NULLIF(%s,''),admin_note),
                approved_at=CASE WHEN %s='approved' THEN NOW() ELSE approved_at END,
                rejected_at=CASE WHEN %s='rejected' THEN NOW() ELSE rejected_at END,
                updated_at=NOW()
              WHERE order_id=%s RETURNING order_id,status,email""",
                (ns,rr,an,ns,ns,oid))
            upd = c.fetchone()
            if not upd:
                conn.rollback()
                return jsonify({"success": False, "error": "Order not found or status unchanged"}), 404
            audit(c, oid, cur["status"], ns, f"admin_override:{an or rr}")
        conn.commit()
        return jsonify({"success": True, "order": dict(upd)}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally: release_db(conn)


# ── ADMIN: BLOCKLIST VIEWS ─────────────────────────────────────────────
@app.route("/api/admin/returns-blocklist", methods=["GET"])
@require_admin
def returns_blocklist():
    conn = get_db()
    if not conn: return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        lim = min(int(request.args.get("limit", 200)), 1000)
        with conn.cursor() as c:
            c.execute("SELECT suborder_id,source_filename,added_at FROM returns_blocklist ORDER BY added_at DESC LIMIT %s", (lim,))
            rows = c.fetchall()
            c.execute("SELECT COUNT(*) as total FROM returns_blocklist")
            total = c.fetchone()["total"]
        return jsonify({"success": True, "total": total, "blocklist": [dict(r) for r in rows]}), 200
    finally: release_db(conn)

@app.route("/api/admin/orders-whitelist", methods=["GET"])
@require_admin
def orders_whitelist():
    conn = get_db()
    if not conn: return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        lim = min(int(request.args.get("limit", 200)), 1000)
        with conn.cursor() as c:
            c.execute("SELECT suborder_id,source_filename,added_at FROM orders_whitelist ORDER BY added_at DESC LIMIT %s", (lim,))
            rows = c.fetchall()
            c.execute("SELECT COUNT(*) as total FROM orders_whitelist")
            total = c.fetchone()["total"]
        return jsonify({"success": True, "total": total, "whitelist": [dict(r) for r in rows]}), 200
    finally: release_db(conn)


# ── ADMIN: CONFIG ──────────────────────────────────────────────────────
@app.route("/api/admin/config", methods=["GET"])
@require_admin
def get_cfg():
    conn = get_db()
    if not conn: return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("SELECT key,value,description,updated_at FROM system_config ORDER BY key")
            return jsonify({"success": True, "config": [dict(r) for r in c.fetchall()]}), 200
    finally: release_db(conn)

@app.route("/api/admin/config", methods=["POST"])
@require_admin
def set_cfg():
    d = request.get_json(silent=True) or {}
    k = d.get("key","").strip(); v = d.get("value","").strip()
    OK = {"cooling_days","auto_approve_enabled","stale_order_days",
          "min_csv_checks_before_approve","max_csv_staleness_days"}
    if k not in OK: return jsonify({"success": False, "error": f"Not editable: {k}"}), 400
    conn = get_db()
    if not conn: return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("UPDATE system_config SET value=%s,updated_at=NOW() WHERE key=%s RETURNING key,value",(v,k))
            upd = c.fetchone()
        conn.commit()
        if not upd: return jsonify({"success": False, "error": "Key not found"}), 404
        return jsonify({"success": True, "config": dict(upd)}), 200
    except Exception as e:
        conn.rollback(); return jsonify({"success": False, "error": str(e)}), 500
    finally: release_db(conn)


# ── ADMIN: SYNC LOGS ───────────────────────────────────────────────────
@app.route("/api/admin/sync-logs", methods=["GET"])
@require_admin
def sync_logs():
    conn = get_db()
    if not conn: return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("SELECT * FROM csv_sync_log ORDER BY synced_at DESC LIMIT 30")
            return jsonify({"success": True, "sync_logs": [dict(r) for r in c.fetchall()]}), 200
    finally: release_db(conn)


# ── API: GET STARS ─────────────────────────────────────────────────────
@app.route("/api/get-stars", methods=["POST"])
def get_stars():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email):
        return jsonify({"success": False, "error": "Invalid email address"}), 400
    conn = get_db()
    if not conn: return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("SELECT total_stars,submission_count,created_at FROM users WHERE lower(email)=lower(%s)", (email,))
            user = c.fetchone()
            if not user: return jsonify({"success": True, "found": False}), 200
            c.execute("""SELECT
                COUNT(*) FILTER(WHERE status='approved')     AS approved,
                COUNT(*) FILTER(WHERE status='pending')      AS pending,
                COUNT(*) FILTER(WHERE status='under_review') AS under_review,
                COUNT(*) FILTER(WHERE status='rejected')     AS rejected,
                COUNT(*) FILTER(WHERE status='disputed')     AS disputed,
                COUNT(*)                                     AS total
              FROM orders WHERE lower(email)=lower(%s)""", (email,))
            counts = c.fetchone() or {}
            c.execute("""SELECT order_id,status,submitted_at,approved_at,token,rejection_reason
              FROM orders WHERE lower(email)=lower(%s)
              ORDER BY submitted_at DESC LIMIT 10""", (email,))
            orders = c.fetchall()
        return jsonify({
            "success": True, "found": True,
            "total_stars":  user.get("total_stars", 0),
            "approved":     counts.get("approved", 0),
            "pending":      counts.get("pending", 0),
            "under_review": counts.get("under_review", 0),
            "rejected":     counts.get("rejected", 0),
            "total_orders": counts.get("total", 0),
            "orders": [{
                "order_id":         o["order_id"],
                "status":           o["status"],
                "submitted":        o["submitted_at"].isoformat() if o.get("submitted_at") else None,
                "approved":         o["approved_at"].isoformat()  if o.get("approved_at")  else None,
                "token":            o["token"],
                "rejection_reason": o.get("rejection_reason"),
            } for o in orders]
        }), 200
    except Exception as e:
        log.error("get_stars: %s", e)
        return jsonify({"success": False, "error": "Server error"}), 500
    finally: release_db(conn)


# ── ADMIN: EXPORT ORDERS ──────────────────────────────────────────────
@app.route("/api/admin/export-orders", methods=["GET"])
@require_admin
def export_orders():
    """
    Export all orders to CSV for download.
    Filter by status if provided via query param.
    """
    try:
        conn = get_db()
        if not conn:
            return jsonify({"success": False, "error": "Database unavailable"}), 500
        
        status_filter = request.args.get("status", "").strip()
        with conn.cursor() as c:
            if status_filter:
                c.execute("""SELECT order_id,email,status,verified_in_orders_csv,submitted_at,
                    approved_at,rejected_at,rejection_reason,admin_note,created_at
                    FROM orders WHERE status=%s::order_status ORDER BY submitted_at DESC""", 
                    (status_filter,))
            else:
                c.execute("""SELECT order_id,email,status,verified_in_orders_csv,submitted_at,
                    approved_at,rejected_at,rejection_reason,admin_note,created_at
                    FROM orders ORDER BY submitted_at DESC""")
            rows = c.fetchall()
        
        if not rows:
            return jsonify({"success": False, "error": "No orders found"}), 404
        
        # Generate CSV
        output = io.StringIO()
        fieldnames = ["Order ID", "Email", "Status", "Verified?", "Submitted", 
                      "Approved", "Rejected", "Rejection Reason", "Admin Note"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            writer.writerow({
                "Order ID": row["order_id"],
                "Email": row["email"],
                "Status": row["status"],
                "Verified?": "Yes" if row["verified_in_orders_csv"] else "No",
                "Submitted": row["submitted_at"].isoformat() if row.get("submitted_at") else "",
                "Approved": row["approved_at"].isoformat() if row.get("approved_at") else "",
                "Rejected": row["rejected_at"].isoformat() if row.get("rejected_at") else "",
                "Rejection Reason": row.get("rejection_reason", "") or "",
                "Admin Note": row.get("admin_note", "") or "",
            })
        
        csv_content = output.getvalue()
        output.close()
        release_db(conn)
        
        return csv_content, 200, {
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f"attachment; filename=orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    except Exception as e:
        log.error("export_orders error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── WAKE / HEALTH ──────────────────────────────────────────────────────
@app.route("/api/wake", methods=["GET"])
def wake():
    conn = get_db()
    if conn: release_db(conn); return jsonify({"status": "ready"}), 200
    return jsonify({"status": "starting"}), 503

@app.route("/health")
@app.route("/api/health")
def health():
    if not DATABASE_URL:
        return jsonify({"status": "unhealthy", "error": "DATABASE_URL missing"}), 500
    return jsonify({"status": "healthy", "database": "supabase", "uptime": "vercel"}), 200

@app.route("/health/db")
def health_db():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as c: c.execute("SELECT 1")
        except Exception:
            release_db(conn)
            return jsonify({"status": "unhealthy"}), 500
        release_db(conn)
        return jsonify({"status": "healthy", "database": "connected"}), 200
    return jsonify({"status": "unhealthy"}), 500


# ── ERROR HANDLERS ─────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(_):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "File too large (max 5MB)"}), 413
    return "File too large", 413

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Not found"}), 404
    return "Not Found", 404


if __name__ == '__main__':
    app.run(debug=True)