# app.py - Vistara Rewards (Production, Free-Plan Edition)
# Free services: Vercel + Supabase + Cloudflare R2 + GitHub Actions
# CSS: static/css/style.css

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os, random, string, hashlib, logging, tempfile
from datetime import datetime, timezone
import re
import psycopg
from psycopg.rows import dict_row
from werkzeug.utils import secure_filename

app  = Flask(__name__)
CORS(app)

# ── SPEED: compress all responses ────────────────────────────────────
try:
    from flask_compress import Compress
    Compress(app)
except ImportError:
    pass

# ── SPEED: cache headers for static files ────────────────────────────
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
DATABASE_URL     = os.getenv("DATABASE_URL")
DB_SSLMODE       = os.getenv("DB_SSLMODE", "require")
ADMIN_SECRET     = os.getenv("ADMIN_SECRET", "")
MAX_FILE_BYTES   = int(os.getenv("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))
ALLOWED_EXTS     = {"png", "jpg", "jpeg", "gif", "webp"}
RATE_WIN_MIN     = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "60"))
RATE_MAX_REQ     = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "5"))

MEESHO_ORDER_ID_REGEX = re.compile(r'^\d{15,19}_\d{1,2}$')

# Cloudflare R2
R2_ON            = os.getenv("R2_ENABLED", "false").lower() == "true"
R2_ACCOUNT_ID    = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY    = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY    = os.getenv("R2_SECRET_KEY", "")
R2_BUCKET        = os.getenv("R2_BUCKET_NAME", "vistara-screenshots")

UPLOAD_DIR = os.getenv("UPLOAD_FOLDER", "/tmp/vistara_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES

# ── RETURN CSV CONFIG ─────────────────────────────────────────────────
# Meesho Returns CSV columns (the download from Returns window)
RETURN_CSV_SUBORDER_COL   = os.getenv("RETURN_CSV_SUBORDER_COL",   "Suborder Number")
RETURN_CSV_TYPE_COL       = os.getenv("RETURN_CSV_TYPE_COL",        "Type of Return")
RETURN_CSV_RETURN_DATE    = os.getenv("RETURN_CSV_RETURN_DATE",     "Return Created Date")

# All return type values that mean "this is a return"
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
    if not DATABASE_URL:
        return
    try:
        from psycopg_pool import ConnectionPool
        _pool = ConnectionPool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            open=True,
            kwargs={
                "sslmode": DB_SSLMODE,
                "connect_timeout": 15,
                "row_factory": dict_row,
            },
        )
        log.info("DB connection pool initialised")
    except Exception as e:
        log.warning("Pool init failed (will use single connections): %s", e)
        _pool = None

with app.app_context():
    init_pool()

def get_db(retries=3):
    global _pool
    import time
    if _pool is not None:
        try:
            conn = _pool.getconn(timeout=10)
            return conn
        except Exception as e:
            log.warning("Pool getconn failed, falling back: %s", e)
    if not DATABASE_URL:
        log.warning("DATABASE_URL not set")
        return None
    for attempt in range(retries):
        try:
            return psycopg.connect(
                DATABASE_URL, sslmode=DB_SSLMODE,
                connect_timeout=15, autocommit=False,
                row_factory=dict_row)
        except Exception as e:
            log.warning("DB direct attempt %d failed: %s", attempt+1, e)
            if attempt < retries - 1:
                time.sleep(2)
    log.error("DB connect failed after %d attempts", retries)
    return None

def get_config(conn) -> dict:
    try:
        with conn.cursor() as c:
            c.execute("SELECT key, value FROM system_config")
            return {r["key"]: r["value"] for r in c.fetchall()}
    except Exception:
        return {}

def audit(cur, order_id, from_s, to_s, reason, sync_id=None):
    try:
        cur.execute("""
            INSERT INTO order_status_log(order_id,from_status,to_status,reason,csv_sync_log_id)
            VALUES(%s,%s,%s,%s,%s)
        """, (order_id, from_s, to_s, reason, sync_id))
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
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY,
                config=Config(signature_version="s3v4"),
                region_name="auto")
            file_obj.seek(0)
            s3.upload_fileobj(file_obj, R2_BUCKET, filename)
            return f"r2://{R2_BUCKET}/{filename}"
        except Exception as e:
            log.error("R2 upload failed, using /tmp: %s", e)
    path = os.path.join(UPLOAD_DIR, filename)
    file_obj.seek(0)
    file_obj.save(path)
    return path


# ── RATE LIMITING ─────────────────────────────────────────────────────
def check_rate(conn, identifier, id_type) -> bool:
    try:
        with conn.cursor() as c:
            c.execute("""
                INSERT INTO rate_limits(identifier,identifier_type,window_start,request_count)
                VALUES(%s,%s,NOW(),1)
                ON CONFLICT(identifier,identifier_type) DO UPDATE SET
                  request_count = CASE
                    WHEN NOW()-rate_limits.window_start > (%s||' minutes')::INTERVAL THEN 1
                    ELSE rate_limits.request_count+1 END,
                  window_start = CASE
                    WHEN NOW()-rate_limits.window_start > (%s||' minutes')::INTERVAL THEN NOW()
                    ELSE rate_limits.window_start END
                RETURNING request_count
            """, (identifier, id_type, RATE_WIN_MIN, RATE_WIN_MIN))
            row = c.fetchone()
            return (row["request_count"] if row else 1) <= RATE_MAX_REQ
    except Exception as e:
        log.warning("rate check fail-open: %s", e)
        return True


# ── RETURN CSV PROCESSOR ──────────────────────────────────────────────
def parse_return_csv(filepath: str) -> set:
    """
    Parse Meesho Returns CSV (downloaded from Returns window).
    Skips the metadata header rows (Supplier ID, name etc.) and
    returns a set of Suborder Numbers (order IDs) that are returns.

    Handles both:
      - Customer Return
      - Courier Return (RTO)
    """
    import csv as csvlib
    returned_ids = set()
    try:
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            lines = f.readlines()

        # Find the actual header row — it contains "Suborder Number"
        header_idx = None
        for i, line in enumerate(lines):
            if RETURN_CSV_SUBORDER_COL in line:
                header_idx = i
                break

        if header_idx is None:
            log.error("Return CSV: could not find '%s' column", RETURN_CSV_SUBORDER_COL)
            return returned_ids

        import io
        content = "".join(lines[header_idx:])
        reader = csvlib.DictReader(io.StringIO(content))

        if RETURN_CSV_SUBORDER_COL not in (reader.fieldnames or []):
            log.error("Return CSV missing '%s'. Got: %s", RETURN_CSV_SUBORDER_COL, reader.fieldnames)
            return returned_ids

        for row in reader:
            suborder = str(row.get(RETURN_CSV_SUBORDER_COL, "")).strip()
            ret_type = str(row.get(RETURN_CSV_TYPE_COL, "")).strip().lower()
            if not suborder:
                continue
            # All rows in this CSV are returns — but double-check type too
            if ret_type in RETURN_TYPE_VALUES or ret_type:
                returned_ids.add(suborder)

        log.info("Return CSV parsed: %d returned order IDs found", len(returned_ids))
    except Exception as e:
        log.error("parse_return_csv error: %s", e)
    return returned_ids


def process_return_csv(filepath: str, conn, sync_id: int) -> dict:
    """
    NEW LOGIC — Simple, accurate, fraud-proof:

    1. Parse the Meesho Returns CSV → extract all returned Suborder Numbers
    2. For each returned order ID found in our DB:
       - REJECT immediately if pending/under_review
       - Mark as DISPUTED if already approved (late return caught)
       - Set ever_showed_return = TRUE permanently
    3. For all other orders NOT in returns CSV:
       - They stay as-is; auto-approve runs separately after cooling days

    This replaces the old delivered-CSV upload flow entirely.
    """
    returned_ids = parse_return_csv(filepath)
    stats = dict(
        rows_processed=len(returned_ids),
        rows_matched=0,
        rows_rejected=0,
        rows_disputed=0,
        rows_skipped=0,
        returned_ids_in_csv=len(returned_ids),
    )

    if not returned_ids:
        log.warning("Return CSV produced 0 IDs — check file format")
        return stats

    for suborder_id in returned_ids:
        with conn.cursor() as c:
            c.execute("""SELECT order_id, status, email
                         FROM orders WHERE order_id = %s""", (suborder_id,))
            order = c.fetchone()

        if not order:
            stats["rows_skipped"] += 1
            continue

        stats["rows_matched"] += 1
        current_status = order["status"]

        with conn.cursor() as c:
            # Always permanently mark ever_showed_return = TRUE
            c.execute("""UPDATE orders SET
                ever_showed_return = TRUE,
                consecutive_delivered_count = 0,
                csv_last_status = 'returned_via_return_csv',
                csv_last_seen_at = NOW(),
                updated_at = NOW()
              WHERE order_id = %s""", (suborder_id,))

            if current_status == "approved":
                # Late return — already gave star, now dispute
                c.execute("""UPDATE orders SET
                    status = 'disputed',
                    admin_note = COALESCE(admin_note || ' | ', '') ||
                                 'LATE RETURN caught via Returns CSV ' || NOW()::DATE::TEXT,
                    updated_at = NOW()
                  WHERE order_id = %s""", (suborder_id,))
                audit(c, suborder_id, "approved", "disputed",
                      "late_return:returns_csv_upload", sync_id)
                stats["rows_disputed"] += 1
                log.warning("DISPUTED late return order_id=%s email=%s",
                            suborder_id, mask(order.get("email", "")))

            elif current_status not in ("rejected", "disputed", "stale"):
                # Pending / under_review → reject immediately
                c.execute("""UPDATE orders SET
                    status = 'rejected',
                    rejected_at = NOW(),
                    rejection_reason = 'Found in Meesho Returns CSV — order was returned',
                    updated_at = NOW()
                  WHERE order_id = %s AND status NOT IN ('rejected', 'disputed')""",
                    (suborder_id,))
                audit(c, suborder_id, current_status, "rejected",
                      "returns_csv:order_found_in_returns", sync_id)
                stats["rows_rejected"] += 1
                log.info("REJECTED via returns CSV order_id=%s status_was=%s",
                         suborder_id, current_status)

        conn.commit()

    log.info("Return CSV processing done: matched=%d rejected=%d disputed=%d skipped=%d",
             stats["rows_matched"], stats["rows_rejected"],
             stats["rows_disputed"], stats["rows_skipped"])
    return stats


def auto_approve_eligible(conn, sync_id: int) -> dict:
    """
    After uploading return CSV, auto-approve orders that:
    - Are under_review
    - NOT in ever_showed_return
    - Have passed cooling_days since first delivered
    """
    cfg   = get_config(conn)
    cool  = int(cfg.get("cooling_days", "21"))
    auto  = cfg.get("auto_approve_enabled", "true").lower() == "true"
    stats = dict(approved=0, checked=0)

    if not auto:
        return stats

    now = datetime.now(timezone.utc)
    with conn.cursor() as c:
        c.execute("""SELECT order_id, email, token, csv_delivered_at,
                            ever_showed_return, submitted_at
                     FROM orders WHERE status = 'under_review'
                       AND ever_showed_return = FALSE""")
        candidates = c.fetchall()

    for o in candidates:
        stats["checked"] += 1
        # Use submitted_at as fallback if csv_delivered_at is missing
        ref_date = o.get("csv_delivered_at") or o.get("submitted_at")
        if not ref_date:
            continue
        days_elapsed = (now - ref_date).days
        if days_elapsed < cool:
            continue
        # Approve
        with conn.cursor() as c:
            c.execute("""UPDATE orders SET status = 'approved',
                approved_at = NOW(), updated_at = NOW()
              WHERE order_id = %s AND status = 'under_review'
              RETURNING order_id""", (o["order_id"],))
            if c.fetchone():
                audit(c, o["order_id"], "under_review", "approved",
                      f"auto_approve_after_returns_csv:days={days_elapsed}", sync_id)
                stats["approved"] += 1
                log.info("APPROVED order_id=%s days=%d", o["order_id"], days_elapsed)
        conn.commit()

    return stats


# ── PAGES ─────────────────────────────────────────────────────────────
@app.route("/")
def index():        return render_template("index.html")

@app.route("/check-stars")
def check_stars():  return render_template("check-stars.html")

@app.route("/admin")
def admin():        return render_template("admin.html")


# ── API: SUBMIT ORDER ─────────────────────────────────────────────────
@app.route("/api/submit", methods=["POST"])
def submit():
    ip = client_ip()
    uh = ua_hash()

    content_len = request.content_length or 0
    if content_len > MAX_FILE_BYTES:
        return jsonify({"success": False, "error": "Request too large. Max 5MB allowed."}), 413

    name     = (request.form.get("name", "") or "").strip()
    email    = (request.form.get("email", "") or "").strip().lower()
    order_id = (request.form.get("order_id", "") or "").strip()

    if not name or not email or not order_id:
        return jsonify({"success": False, "error": "All fields are required."}), 400

    if len(name) < 2:
        return jsonify({"success": False, "error": "Name must be at least 2 characters."}), 400
    if len(name) > 100:
        return jsonify({"success": False, "error": "Name too long."}), 400
    if not re.match(r'^[ऀ-ॿ਀-੿଀-୿a-zA-Z\s.\'-]+$', name):
        return jsonify({"success": False, "error": "Name contains invalid characters."}), 400

    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email):
        return jsonify({"success": False, "error": "Invalid email address."}), 400
    if len(email) > 254:
        return jsonify({"success": False, "error": "Email address too long."}), 400

    if not MEESHO_ORDER_ID_REGEX.match(order_id):
        return jsonify({"success": False,
            "error": "Invalid Order ID format. Meesho Order IDs look like: 265437129718567616_1"}), 400

    of = request.files.get("order_screenshot")
    if not of or not of.filename:
        return jsonify({"success": False, "error": "Order screenshot is required."}), 400
    if not ok_ext(of.filename):
        return jsonify({"success": False, "error": "Screenshot must be PNG, JPG, GIF or WEBP."}), 400
    file_bytes = of.read()
    if len(file_bytes) == 0:
        return jsonify({"success": False, "error": "Screenshot file is empty."}), 400
    if len(file_bytes) > MAX_FILE_BYTES:
        return jsonify({"success": False, "error": "Screenshot too large. Max 5MB."}), 413
    MAGIC = {
        b'\xff\xd8\xff': "jpg",
        b'\x89PNG':       "png",
        b'GIF8':          "gif",
        b'RIFF':          "webp",
    }
    if not any(file_bytes[:len(sig)] == sig for sig in MAGIC):
        return jsonify({"success": False, "error": "File does not appear to be a valid image."}), 400
    of.seek(0)

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable. Try again shortly."}), 500

    try:
        with conn.cursor() as c:
            c.execute("""SELECT 1 FROM blocked_entities
                         WHERE entity_type='ip' AND value=%s LIMIT 1""", (ip,))
            if c.fetchone():
                return jsonify({"success": False,
                    "error": "Access denied. Contact support if you believe this is an error."}), 403

            c.execute("""SELECT 1 FROM blocked_entities
                         WHERE entity_type='email' AND lower(value)=lower(%s) LIMIT 1""", (email,))
            if c.fetchone():
                return jsonify({"success": False,
                    "error": "This email has been restricted. Contact support."}), 403

            if not check_rate(conn, ip, "ip"):
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False,
                    "error": "Too many submissions from your device. Please wait an hour."}), 429

            if not check_rate(conn, email, "email"):
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False,
                    "error": "Too many submissions from this email. Please wait an hour."}), 429

            c.execute("""SELECT COUNT(*) as cnt FROM orders
                         WHERE lower(email)=lower(%s)
                         AND submitted_at > NOW() - INTERVAL '24 hours'""", (email,))
            daily_count = (c.fetchone() or {}).get("cnt", 0)
            if daily_count >= 3:
                return jsonify({"success": False,
                    "error": "Maximum 3 orders can be submitted per day from one email."}), 429

            # ── CHECK RETURNS DB TABLE FIRST ─────────────────────────
            # If this order_id is already in our returns_blocklist table → reject instantly
            c.execute("""SELECT 1 FROM returns_blocklist
                         WHERE suborder_id = %s LIMIT 1""", (order_id,))
            if c.fetchone():
                _log_attempt(conn, ip, email, order_id, blocked=True)
                log.warning("Submit blocked — order in returns_blocklist order_id=%s", order_id)
                return jsonify({"success": False,
                    "error": "This order was returned and is not eligible for stars."}), 409

            c.execute("""SELECT status, email FROM orders
                         WHERE lower(order_id)=lower(%s) LIMIT 1""", (order_id,))
            existing = c.fetchone()
            if existing:
                _log_attempt(conn, ip, email, order_id, was_duplicate=True)
                return jsonify({"success": False,
                    "error": "This Order ID has already been submitted and is being tracked. "
                             "Each order can only earn stars once."}), 409

            c.execute("""SELECT COUNT(*) as cnt FROM orders
                         WHERE lower(email)=lower(%s)
                         AND submitted_at > NOW() - INTERVAL '7 days'""", (email,))
            week_count = (c.fetchone() or {}).get("cnt", 0)

            c.execute("""SELECT COUNT(DISTINCT lower(email)) as cnt FROM orders
                         WHERE ip_address=%s
                         AND submitted_at > NOW() - INTERVAL '24 hours'""", (ip,))
            ip_email_count = (c.fetchone() or {}).get("cnt", 0)

            fraud_score = 0
            fraud_reasons = []

            if ip_email_count >= 3:
                fraud_score += 30
                fraud_reasons.append(f"ip_multi_email:{ip_email_count}")
            if week_count >= 5:
                fraud_score += 20
                fraud_reasons.append(f"high_weekly_volume:{week_count}")
            if daily_count >= 2:
                fraud_score += 10
                fraud_reasons.append(f"daily_count:{daily_count}")

            c.execute("""SELECT COUNT(*) as cnt FROM submission_attempts
                         WHERE ip_address=%s
                         AND attempted_at > NOW() - INTERVAL '1 hour'
                         AND (was_duplicate OR was_invalid_fmt OR blocked)""", (ip,))
            bad_attempts = (c.fetchone() or {}).get("cnt", 0)
            if bad_attempts >= 5:
                fraud_score += 25
                fraud_reasons.append(f"bad_attempts:{bad_attempts}")

            if fraud_score >= 80:
                try:
                    c.execute("""INSERT INTO blocked_entities(entity_type, value, reason)
                                 VALUES('ip', %s, %s)
                                 ON CONFLICT(entity_type, value) DO NOTHING""",
                              (ip, f"Auto-blocked: fraud_score={fraud_score}"))
                    conn.commit()
                except Exception:
                    pass
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False,
                    "error": "Suspicious activity detected. Access temporarily restricted."}), 403

        pfx = random.randint(10000, 99999)
        op  = save_file(of, f"{pfx}_{secure_filename(of.filename)}")
        rp  = None
        rf  = request.files.get("rating_screenshot")
        if rf and rf.filename and ok_ext(rf.filename):
            rf_bytes = rf.read()
            if 0 < len(rf_bytes) <= MAX_FILE_BYTES:
                rf.seek(0)
                rp = save_file(rf, f"{pfx}r_{secure_filename(rf.filename)}")

        with conn.cursor() as c:
            c.execute("""INSERT INTO users(email)
                         VALUES(%s)
                         ON CONFLICT(email) DO UPDATE SET updated_at=NOW()
                         RETURNING total_stars""", (email,))
            stars = (c.fetchone() or {}).get("total_stars", 0)

        token = None
        for _ in range(10):
            t = gen_token()
            try:
                with conn.cursor() as c:
                    c.execute("""INSERT INTO orders(
                        order_id, email, name, token, status,
                        screenshot_order_path, screenshot_rating_path,
                        ip_address, user_agent_hash, submitted_at,
                        fraud_score, fraud_reasons, submission_count_snapshot)
                      VALUES(%s,%s,%s,%s,'pending',%s,%s,%s,%s,NOW(),%s,%s,%s)""",
                        (order_id, email, name, t, op, rp, ip, uh,
                         fraud_score, ",".join(fraud_reasons) if fraud_reasons else None,
                         week_count))
                token = t
                break
            except Exception as e:
                if "unique" in str(e).lower():
                    conn.rollback()
                    continue
                raise

        if not token:
            conn.rollback()
            return jsonify({"success": False, "error": "Token error — please retry."}), 500

        _log_attempt(conn, ip, email, order_id)
        conn.commit()

        log.info("submit_ok email=%s order_id=%s fraud_score=%d", mask(email), order_id, fraud_score)
        return jsonify({
            "success": True,
            "token": token,
            "total_stars": stars,
            "message": "Order submitted! Stars added after delivery is confirmed (14–21 days)."
        }), 200

    except Exception as e:
        try: conn.rollback()
        except Exception: pass
        log.error("submit_db: %s", e)
        return jsonify({"success": False, "error": "Server error. Please try again."}), 500
    finally:
        try: conn.close()
        except Exception: pass


def _log_attempt(conn, ip, email, order_id,
                 was_duplicate=False, was_invalid_fmt=False, blocked=False):
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO submission_attempts
                         (ip_address, email, order_id, was_duplicate, was_invalid_fmt, blocked)
                         VALUES(%s, %s, %s, %s, %s, %s)""",
                      (ip, email, order_id, was_duplicate, was_invalid_fmt, blocked))
        conn.commit()
    except Exception as ex:
        log.warning("log_attempt_error: %s", ex)


# ── ADMIN: UPLOAD RETURNS CSV ─────────────────────────────────────────
@app.route("/api/admin/upload-returns-csv", methods=["POST"])
@require_admin
def upload_returns_csv():
    """
    Upload Meesho Returns CSV (from Returns window download).
    Logic:
      1. Parse all Suborder Numbers from the CSV
      2. Store them in returns_blocklist table
      3. Reject/dispute any matching orders in our DB
      4. Auto-approve eligible orders not in returns CSV
    """
    if "csv_file" not in request.files:
        return jsonify({"success": False, "error": "csv_file required"}), 400
    f = request.files["csv_file"]
    if not f.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "error": "Must be .csv"}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO csv_sync_log(filename, synced_by)
                         VALUES(%s, 'returns_csv_upload') RETURNING id""", (f.filename,))
            sid = c.fetchone()["id"]
        conn.commit()

        # Step 1: Parse returns CSV to get all returned suborder IDs
        returned_ids = parse_return_csv(tmp_path)

        # Step 2: Store ALL returned IDs in returns_blocklist (for future submit checks)
        if returned_ids:
            with conn.cursor() as c:
                for rid in returned_ids:
                    c.execute("""INSERT INTO returns_blocklist(suborder_id, source_filename, added_at)
                                 VALUES(%s, %s, NOW())
                                 ON CONFLICT(suborder_id) DO UPDATE SET
                                   source_filename = EXCLUDED.source_filename,
                                   added_at = NOW()""", (rid, f.filename))
            conn.commit()
            log.info("Stored %d returned IDs in returns_blocklist", len(returned_ids))

        # Step 3: Process — reject/dispute matched orders
        stats = process_return_csv(tmp_path, conn, sid)

        # Step 4: Auto-approve orders NOT in returns (that passed cooling days)
        approve_stats = auto_approve_eligible(conn, sid)
        stats["auto_approved"] = approve_stats["approved"]
        stats["auto_approve_checked"] = approve_stats["checked"]

        # Step 5: Update sync log
        with conn.cursor() as c:
            c.execute("""UPDATE csv_sync_log SET
                rows_processed=%s, rows_matched=%s,
                rows_returned=%s, rows_approved=%s, rows_disputed=%s, rows_skipped=%s
              WHERE id=%s""",
                (stats["rows_processed"], stats["rows_matched"],
                 stats["rows_rejected"], stats.get("auto_approved", 0),
                 stats["rows_disputed"], stats["rows_skipped"], sid))
        conn.commit()

        return jsonify({
            "success": True,
            "stats": stats,
            "sync_log_id": sid,
            "message": (
                f"✅ Returns CSV processed: "
                f"{stats['returned_ids_in_csv']} returned IDs found, "
                f"{stats['rows_matched']} matched in DB, "
                f"{stats['rows_rejected']} rejected, "
                f"{stats['rows_disputed']} disputed, "
                f"{stats.get('auto_approved',0)} auto-approved."
            )
        }), 200

    except Exception as e:
        conn.rollback()
        log.error("upload_returns_csv: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()
        try: os.unlink(tmp_path)
        except Exception: pass


# ── ADMIN: RUN APPROVALS (GitHub Actions daily) ───────────────────────
@app.route("/api/admin/run-approvals", methods=["POST"])
@require_admin
def run_approvals():
    """GitHub Actions calls this daily at 3 AM IST."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO csv_sync_log(filename, synced_by)
                         VALUES('github_actions_daily', 'github_actions') RETURNING id""")
            sid = c.fetchone()["id"]
        conn.commit()

        approve_stats = auto_approve_eligible(conn, sid)

        return jsonify({
            "success": True,
            "approved_count": approve_stats["approved"],
            "checked_count": approve_stats["checked"],
            "message": f"Daily run: {approve_stats['approved']} approved of {approve_stats['checked']} checked"
        }), 200
    except Exception as e:
        conn.rollback()
        log.error("run_approvals: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ── ADMIN: MARK STALE ─────────────────────────────────────────────────
@app.route("/api/admin/mark-stale", methods=["POST"])
@require_admin
def mark_stale():
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        days = int(get_config(conn).get("stale_order_days", "45"))
        with conn.cursor() as c:
            c.execute("""UPDATE orders SET status='stale',
                admin_note=COALESCE(admin_note||' | ','')||'Auto-stale after '||%s||' days',
                updated_at=NOW()
              WHERE status='pending'
                AND submitted_at < NOW()-(%s||' days')::INTERVAL
              RETURNING order_id""", (str(days), str(days)))
            rows = c.fetchall()
        conn.commit()
        return jsonify({"success": True, "marked_count": len(rows)}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ── ADMIN: PING ────────────────────────────────────────────────────────
@app.route("/api/admin/ping", methods=["POST"])
@require_admin
def admin_ping():
    conn = get_db()
    counts = {}
    if conn:
        try:
            with conn.cursor() as c:
                c.execute("""SELECT
                    COUNT(*) FILTER(WHERE status='pending')      AS pending,
                    COUNT(*) FILTER(WHERE status='under_review') AS under_review,
                    COUNT(*) FILTER(WHERE status='approved')     AS approved,
                    COUNT(*) FILTER(WHERE status='rejected')     AS rejected,
                    COUNT(*) FILTER(WHERE status='disputed')     AS disputed,
                    COUNT(*) FILTER(WHERE status='stale')        AS stale
                  FROM orders""")
                counts = dict(c.fetchone() or {})
        except Exception:
            pass
        finally:
            conn.close()
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
                c.execute("SELECT * FROM v_admin_orders WHERE status=%s::order_status LIMIT %s OFFSET %s", (sf, lim, off))
            else:
                c.execute("SELECT * FROM v_admin_orders LIMIT %s OFFSET %s", (lim, off))
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
        return jsonify({"success": True, "orders": [dict(r) for r in rows],
                        "counts": dict(counts) if counts else {}}), 200
    finally:
        conn.close()


# ── ADMIN: UPDATE ORDER ────────────────────────────────────────────────
@app.route("/api/admin/update-order", methods=["POST"])
@require_admin
def update_order():
    d   = request.get_json(silent=True) or {}
    oid = d.get("order_id", "").strip()
    ns  = d.get("status", "").strip()
    rr  = d.get("rejection_reason", "").strip()
    an  = d.get("admin_note", "").strip()
    VALID = {"pending", "under_review", "approved", "rejected", "flagged", "disputed"}
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
            if not cur:
                return jsonify({"success": False, "error": "Not found"}), 404
            c.execute("""UPDATE orders SET
                status=%s::order_status,
                rejection_reason=COALESCE(NULLIF(%s,''),rejection_reason),
                admin_note=COALESCE(NULLIF(%s,''),admin_note),
                approved_at=CASE WHEN %s='approved' THEN NOW() ELSE approved_at END,
                rejected_at=CASE WHEN %s='rejected' THEN NOW() ELSE rejected_at END,
                updated_at=NOW()
              WHERE order_id=%s RETURNING order_id,status,email""",
                (ns, rr, an, ns, ns, oid))
            upd = c.fetchone()
            audit(c, oid, cur["status"], ns, f"admin_override:{an or rr}")
        conn.commit()
        return jsonify({"success": True, "order": dict(upd)}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ── ADMIN: RETURNS BLOCKLIST ───────────────────────────────────────────
@app.route("/api/admin/returns-blocklist", methods=["GET"])
@require_admin
def returns_blocklist():
    """View all order IDs in the returns blocklist."""
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        lim = min(int(request.args.get("limit", 200)), 1000)
        with conn.cursor() as c:
            c.execute("""SELECT suborder_id, source_filename, added_at
                         FROM returns_blocklist
                         ORDER BY added_at DESC LIMIT %s""", (lim,))
            rows = c.fetchall()
            c.execute("SELECT COUNT(*) as total FROM returns_blocklist")
            total = c.fetchone()["total"]
        return jsonify({
            "success": True,
            "total": total,
            "blocklist": [dict(r) for r in rows]
        }), 200
    finally:
        conn.close()


# ── ADMIN: CONFIG ──────────────────────────────────────────────────────
@app.route("/api/admin/config", methods=["GET"])
@require_admin
def get_cfg():
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("SELECT key,value,description,updated_at FROM system_config ORDER BY key")
            return jsonify({"success": True, "config": [dict(r) for r in c.fetchall()]}), 200
    finally:
        conn.close()

@app.route("/api/admin/config", methods=["POST"])
@require_admin
def set_cfg():
    d = request.get_json(silent=True) or {}
    k = d.get("key", "").strip()
    v = d.get("value", "").strip()
    OK = {"cooling_days", "min_csv_checks_before_approve",
          "max_csv_staleness_days", "auto_approve_enabled", "stale_order_days"}
    if k not in OK:
        return jsonify({"success": False, "error": f"Not editable: {k}"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("UPDATE system_config SET value=%s,updated_at=NOW() WHERE key=%s RETURNING key,value", (v, k))
            upd = c.fetchone()
        conn.commit()
        if not upd:
            return jsonify({"success": False, "error": "Key not found"}), 404
        return jsonify({"success": True, "config": dict(upd)}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ── ADMIN: SYNC LOGS ───────────────────────────────────────────────────
@app.route("/api/admin/sync-logs", methods=["GET"])
@require_admin
def sync_logs():
    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500
    try:
        with conn.cursor() as c:
            c.execute("SELECT * FROM csv_sync_log ORDER BY synced_at DESC LIMIT 30")
            return jsonify({"success": True, "sync_logs": [dict(r) for r in c.fetchall()]}), 200
    finally:
        conn.close()


# ── API: GET STARS ─────────────────────────────────────────────────────
@app.route("/api/get-stars", methods=["POST"])
def get_stars():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email):
        return jsonify({"success": False, "error": "Invalid email address"}), 400

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable"}), 500

    try:
        with conn.cursor() as c:
            c.execute("""SELECT total_stars, submission_count, created_at
                FROM users WHERE lower(email)=lower(%s)""", (email,))
            user = c.fetchone()
            if not user:
                return jsonify({"success": True, "found": False}), 200

            c.execute("""SELECT
                  COUNT(*) FILTER(WHERE status='approved')      AS approved,
                  COUNT(*) FILTER(WHERE status='pending')       AS pending,
                  COUNT(*) FILTER(WHERE status='under_review')  AS under_review,
                  COUNT(*) FILTER(WHERE status='rejected')      AS rejected,
                  COUNT(*) FILTER(WHERE status='disputed')      AS disputed,
                  COUNT(*) FILTER(WHERE status='stale')         AS stale,
                  COUNT(*)                                      AS total
                FROM orders WHERE lower(email)=lower(%s)""", (email,))
            counts = c.fetchone() or {}

            c.execute("""SELECT order_id, status, submitted_at, approved_at,
                               token, rejection_reason
                FROM orders WHERE lower(email)=lower(%s)
                ORDER BY submitted_at DESC LIMIT 10""", (email,))
            orders = c.fetchall()

        return jsonify({
            "success":      True,
            "found":        True,
            "total_stars":  user.get("total_stars", 0),
            "approved":     counts.get("approved", 0),
            "pending":      counts.get("pending", 0),
            "under_review": counts.get("under_review", 0),
            "rejected":     counts.get("rejected", 0),
            "total_orders": counts.get("total", 0),
            "orders": [
                {
                    "order_id":  o["order_id"],
                    "status":    o["status"],
                    "submitted": o["submitted_at"].isoformat() if o.get("submitted_at") else None,
                    "approved":  o["approved_at"].isoformat()  if o.get("approved_at")  else None,
                    "token":     o["token"],
                    "rejection_reason": o.get("rejection_reason"),
                }
                for o in orders
            ]
        }), 200

    except Exception as e:
        log.error("get_stars: %s", e)
        return jsonify({"success": False, "error": "Server error"}), 500
    finally:
        conn.close()


# ── WAKE ───────────────────────────────────────────────────────────────
@app.route("/api/wake", methods=["GET"])
def wake():
    conn = get_db()
    if conn:
        conn.close()
        return jsonify({"status": "ready"}), 200
    return jsonify({"status": "starting"}), 503


# ── HEALTH ─────────────────────────────────────────────────────────────
@app.route("/health")
@app.route("/api/health")
def health():
    if not DATABASE_URL:
        return jsonify({"status": "unhealthy", "error": "DATABASE_URL missing"}), 500
    return jsonify({
        "status":     "healthy",
        "database":   "supabase",
        "automation": "github_actions",
        "uptime":     "vercel"
    }), 200

@app.route("/health/db")
def health_db():
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as c:
                c.execute("SELECT 1")
        except Exception:
            conn.close()
            return jsonify({"status": "unhealthy", "database": "error"}), 500
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    return jsonify({"status": "unhealthy", "database": "disconnected"}), 500


# ── ERROR HANDLERS ─────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(_):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "File too large (max 5 MB)"}), 413
    return "File too large", 413

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Not found"}), 404
    return "Not Found", 404


if __name__ == '__main__':
    app.run(debug=True)