# app.py - Vistara Rewards (Production, Free-Plan Edition)
# Free services: Render + Supabase + Cloudflare R2 + GitHub Actions + UptimeRobot
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
    pass  # optional, install flask-compress for faster responses

# ── SPEED: cache headers for static files ────────────────────────────
@app.after_request
def add_cache_headers(response):
    # Cache static assets for 1 hour, never cache API responses
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

# Meesho Order ID — only valid format: 15-19 digits, underscore, 1-2 digits
# Example: 265437129718567616_1
MEESHO_ORDER_ID_REGEX = re.compile(r'^\d{15,19}_\d{1,2}$')

# Cloudflare R2 (free 10 GB — S3-compatible)
R2_ON            = os.getenv("R2_ENABLED", "false").lower() == "true"
R2_ACCOUNT_ID    = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY    = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY    = os.getenv("R2_SECRET_KEY", "")
R2_BUCKET        = os.getenv("R2_BUCKET_NAME", "vistara-screenshots")

UPLOAD_DIR = os.getenv("UPLOAD_FOLDER", "/tmp/vistara_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_BYTES

# CSV column names (matches Meesho export headers)
CSV_COL_ORDER_ID    = os.getenv("CSV_COL_ORDER_ID",    "Order ID")
CSV_COL_STATUS      = os.getenv("CSV_COL_STATUS",       "Order Status")
CSV_COL_DELIVERY_DT = os.getenv("CSV_COL_DELIVERED_AT", "Delivery Date")

DELIVERED_STATUSES = {"delivered", "delivered to customer"}
RETURNED_STATUSES  = {
    "returned", "rto", "rto delivered", "return delivered",
    "return initiated", "cancelled", "lost in transit",
    "return in transit", "rto initiated",
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
# ── CONNECTION POOL — keeps 2 persistent connections, never sleeps ────
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

# Initialise pool at startup
with app.app_context():
    init_pool()

def get_db(retries=3):
    """Return a DB connection — from pool if available, else direct."""
    global _pool
    import time

    # Try pool first
    if _pool is not None:
        try:
            conn = _pool.getconn(timeout=10)
            return conn
        except Exception as e:
            log.warning("Pool getconn failed, falling back: %s", e)

    # Fallback: direct connection with retries
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
    """R2 if configured, else /tmp (ephemeral — set up R2 for production)."""
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


# ── CSV APPROVAL GATE ─────────────────────────────────────────────────
def can_approve(order: dict, cooling: int, min_checks: int, max_stale: int) -> bool:
    """
    ALL four conditions must pass simultaneously.

    1. ever_showed_return = FALSE  — permanent. Returns reset this field, never unset.
    2. cooling days elapsed        — 21d = 7d return window + 10d transit + 4d CSV lag
    3. consecutive streak >= 3     — 3 separate CSV uploads all showed Delivered (not just total)
                                     streak resets to 0 the instant any CSV shows Returned
    4. csv_last_seen_at fresh      — data must be from a recent upload, not stale
    """
    now = datetime.now(timezone.utc)
    if order["ever_showed_return"]:                           return False
    if not order["csv_delivered_at"]:                         return False
    if (now - order["csv_delivered_at"]).days < cooling:      return False
    if order["consecutive_delivered_count"] < min_checks:     return False
    if not order["csv_last_seen_at"]:                         return False
    if (now - order["csv_last_seen_at"]).days > max_stale:    return False
    return True

def parse_date(s):
    if not s or not s.strip(): return None
    for fmt in ("%Y-%m-%d","%d-%m-%Y","%d/%m/%Y","%Y/%m/%d","%d %b %Y","%d-%b-%Y"):
        try: return datetime.strptime(s.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError: pass
    return None

def process_csv(filepath: str, conn, sync_id: int) -> dict:
    """
    Core fraud-safe CSV processor.

    PATH A — Returned/RTO/Cancelled:
      • Reset consecutive_delivered_count to 0
      • Set ever_showed_return = TRUE (permanent, never resets)
      • Reject immediately; if already approved → disputed

    PATH B — Delivered:
      • Increment consecutive_delivered_count (streak)
      • Start cooling if first time
      • Run approval gate after update

    PATH C — Unknown (Shipped, Out for Delivery…):
      • Update last_seen timestamp only, no status change
    """
    import csv as csvlib
    stats = dict(rows_processed=0, rows_matched=0, rows_delivered=0,
                 rows_returned=0, rows_approved=0, rows_skipped=0, rows_disputed=0)
    cfg   = get_config(conn)
    cool  = int(cfg.get("cooling_days","21"))
    minck = int(cfg.get("min_csv_checks_before_approve","3"))
    stale = int(cfg.get("max_csv_staleness_days","5"))
    auto  = cfg.get("auto_approve_enabled","true").lower() == "true"

    try:
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csvlib.DictReader(f)
            hdrs   = reader.fieldnames or []
            if CSV_COL_ORDER_ID not in hdrs or CSV_COL_STATUS not in hdrs:
                log.error("CSV missing required columns. Got: %s", hdrs)
                return stats
            has_dt = CSV_COL_DELIVERY_DT in hdrs
            rows   = list(reader)
    except Exception as e:
        log.error("CSV read error: %s", e)
        return stats

    log.info("Processing %d CSV rows", len(rows))

    for row in rows:
        stats["rows_processed"] += 1
        oid  = str(row.get(CSV_COL_ORDER_ID,"")).strip()
        raw  = str(row.get(CSV_COL_STATUS,"")).strip()
        cst  = raw.lower().strip()
        rdt  = row.get(CSV_COL_DELIVERY_DT,"") if has_dt else ""
        if not oid:
            stats["rows_skipped"] += 1
            continue

        with conn.cursor() as c:
            c.execute("""SELECT status, csv_delivered_at, csv_check_count,
                                consecutive_delivered_count, ever_showed_return, csv_last_seen_at
                         FROM orders WHERE order_id=%s""", (oid,))
            order = c.fetchone()
        if not order:
            stats["rows_skipped"] += 1
            continue

        stats["rows_matched"] += 1
        dbs = order["status"]

        # ── PATH A: RETURN ────────────────────────────────────────────
        if cst in RETURNED_STATUSES:
            stats["rows_returned"] += 1
            with conn.cursor() as c:
                c.execute("""UPDATE orders SET
                    csv_last_status=%(s)s, csv_last_seen_at=NOW(),
                    csv_check_count=csv_check_count+1,
                    consecutive_delivered_count=0,
                    ever_showed_return=TRUE, updated_at=NOW()
                  WHERE order_id=%(o)s""", {"s": raw, "o": oid})
                if dbs == "approved":
                    c.execute("""UPDATE orders SET status='disputed',
                        admin_note=COALESCE(admin_note||' | ','')
                                  ||'LATE RETURN '||NOW()::DATE::TEXT,
                        updated_at=NOW() WHERE order_id=%s""", (oid,))
                    audit(c, oid, "approved", "disputed", f"late_return:{raw}", sync_id)
                    stats["rows_disputed"] += 1
                    log.warning("DISPUTED late return order_id=%s", oid)
                elif dbs not in ("rejected","disputed","stale"):
                    c.execute("""UPDATE orders SET status='rejected',
                        rejected_at=NOW(), rejection_reason=%s, updated_at=NOW()
                      WHERE order_id=%s AND status NOT IN ('rejected','disputed')""",
                        (f"Meesho CSV: {raw}", oid))
                    audit(c, oid, dbs, "rejected", f"csv:{raw}", sync_id)
                    log.info("REJECTED order_id=%s reason=%s", oid, raw)
            conn.commit()
            continue

        # ── PATH B: DELIVERED ─────────────────────────────────────────
        if cst in DELIVERED_STATUSES:
            del_ts = parse_date(rdt) or datetime.now(timezone.utc)
            with conn.cursor() as c:
                if dbs == "pending":
                    c.execute("""UPDATE orders SET status='under_review',
                        csv_last_status=%(s)s, csv_last_seen_at=NOW(),
                        csv_delivered_at=%(dt)s,
                        csv_check_count=csv_check_count+1,
                        consecutive_delivered_count=consecutive_delivered_count+1,
                        review_started_at=NOW(), updated_at=NOW()
                      WHERE order_id=%(o)s AND status='pending'""",
                        {"s": raw, "dt": del_ts, "o": oid})
                    audit(c, oid, "pending", "under_review", "csv:delivered — cooling started", sync_id)
                    stats["rows_delivered"] += 1
                    log.info("DELIVERED order_id=%s → under_review", oid)
                elif dbs == "under_review":
                    c.execute("""UPDATE orders SET
                        csv_last_status=%s, csv_last_seen_at=NOW(),
                        csv_check_count=csv_check_count+1,
                        consecutive_delivered_count=consecutive_delivered_count+1,
                        updated_at=NOW() WHERE order_id=%s""", (raw, oid))
                    stats["rows_skipped"] += 1
                else:
                    c.execute("""UPDATE orders SET csv_last_status=%s,
                        csv_last_seen_at=NOW(), updated_at=NOW()
                      WHERE order_id=%s""", (raw, oid))
                    stats["rows_skipped"] += 1
            conn.commit()

            # ── APPROVAL GATE (runs after every Delivered update) ─────
            if dbs == "under_review" and auto:
                with conn.cursor() as c:
                    c.execute("""SELECT csv_delivered_at, consecutive_delivered_count,
                                        ever_showed_return, csv_last_seen_at
                                 FROM orders WHERE order_id=%s""", (oid,))
                    fresh = c.fetchone()
                if fresh and can_approve(fresh, cool, minck, stale):
                    with conn.cursor() as c:
                        c.execute("""UPDATE orders SET status='approved',
                            approved_at=NOW(), updated_at=NOW()
                          WHERE order_id=%s AND status='under_review'
                          RETURNING order_id""", (oid,))
                        if c.fetchone():
                            audit(c, oid, "under_review", "approved",
                                  f"auto_approve:cool={cool}d "
                                  f"checks={fresh['consecutive_delivered_count']}", sync_id)
                            stats["rows_approved"] += 1
                            log.info("APPROVED order_id=%s checks=%d",
                                     oid, fresh["consecutive_delivered_count"])
                    conn.commit()
            continue

        # ── PATH C: UNKNOWN STATUS ────────────────────────────────────
        with conn.cursor() as c:
            c.execute("UPDATE orders SET csv_last_status=%s, csv_last_seen_at=NOW(),"
                      " updated_at=NOW() WHERE order_id=%s", (raw, oid))
        conn.commit()
        stats["rows_skipped"] += 1

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

    # ── LAYER 1: File size check (before anything else) ──────────────────
    content_len = request.content_length or 0
    if content_len > MAX_FILE_BYTES:
        return jsonify({"success": False, "error": "Request too large. Max 5MB allowed."}), 413

    # ── LAYER 2: Extract and sanitise inputs ─────────────────────────────
    name     = (request.form.get("name", "") or "").strip()
    email    = (request.form.get("email", "") or "").strip().lower()
    order_id = (request.form.get("order_id", "") or "").strip()

    # ── LAYER 3: Field presence check ────────────────────────────────────
    if not name or not email or not order_id:
        return jsonify({"success": False, "error": "All fields are required."}), 400

    # ── LAYER 4: Name validation ──────────────────────────────────────────
    if len(name) < 2:
        return jsonify({"success": False, "error": "Name must be at least 2 characters."}), 400
    if len(name) > 100:
        return jsonify({"success": False, "error": "Name too long."}), 400
    if not re.match(r'^[ऀ-ॿ਀-੿଀-୿a-zA-Z\s.\'-]+$', name):
        return jsonify({"success": False, "error": "Name contains invalid characters."}), 400

    # ── LAYER 5: Email validation ─────────────────────────────────────────
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email):
        return jsonify({"success": False, "error": "Invalid email address."}), 400
    if len(email) > 254:
        return jsonify({"success": False, "error": "Email address too long."}), 400

    # ── LAYER 6: Meesho Order ID format validation ────────────────────────
    # Only valid format: 15-19 digits, underscore, 1-2 digits
    # Example: 265437129718567616_1
    if not MEESHO_ORDER_ID_REGEX.match(order_id):
        return jsonify({"success": False,
            "error": "Invalid Order ID format. Meesho Order IDs look like: 265437129718567616_1"}), 400

    # ── LAYER 7: Screenshot file validation ───────────────────────────────
    of = request.files.get("order_screenshot")
    if not of or not of.filename:
        return jsonify({"success": False, "error": "Order screenshot is required."}), 400
    if not ok_ext(of.filename):
        return jsonify({"success": False, "error": "Screenshot must be PNG, JPG, GIF or WEBP."}), 400
    # Read file to check actual size and magic bytes
    file_bytes = of.read()
    if len(file_bytes) == 0:
        return jsonify({"success": False, "error": "Screenshot file is empty."}), 400
    if len(file_bytes) > MAX_FILE_BYTES:
        return jsonify({"success": False, "error": "Screenshot too large. Max 5MB."}), 413
    # Validate magic bytes (actual file type, not just extension)
    MAGIC = {
        b'\xff\xd8\xff': "jpg",      # JPEG
        b'\x89PNG':        "png",      # PNG
        b'GIF8':           "gif",      # GIF
        b'RIFF':           "webp",     # WEBP (starts with RIFF)
    }
    file_type_valid = any(file_bytes[:len(sig)] == sig for sig in MAGIC)
    if not file_type_valid:
        return jsonify({"success": False, "error": "File does not appear to be a valid image."}), 400
    # Seek back so we can save it
    of.seek(0)

    conn = get_db()
    if not conn:
        return jsonify({"success": False, "error": "Database unavailable. Try again shortly."}), 500

    try:
        with conn.cursor() as c:

            # ── LAYER 8: Check if IP is blocked ───────────────────────────
            c.execute("""SELECT 1 FROM blocked_entities
                         WHERE entity_type='ip' AND value=%s LIMIT 1""", (ip,))
            if c.fetchone():
                log.warning("blocked_ip attempt ip=%s order_id=%s", ip, order_id)
                return jsonify({"success": False,
                    "error": "Access denied. Contact support if you believe this is an error."}), 403

            # ── LAYER 9: Check if email is blocked ────────────────────────
            c.execute("""SELECT 1 FROM blocked_entities
                         WHERE entity_type='email' AND lower(value)=lower(%s) LIMIT 1""", (email,))
            if c.fetchone():
                log.warning("blocked_email attempt email=%s order_id=%s", mask(email), order_id)
                return jsonify({"success": False,
                    "error": "This email has been restricted. Contact support."}), 403

            # ── LAYER 10: Rate limit by IP (5 submissions per hour) ───────
            if not check_rate(conn, ip, "ip"):
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False,
                    "error": "Too many submissions from your device. Please wait an hour."}), 429

            # ── LAYER 11: Rate limit by email (3 submissions per hour) ────
            if not check_rate(conn, email, "email"):
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False,
                    "error": "Too many submissions from this email. Please wait an hour."}), 429

            # ── LAYER 12: Check daily submission cap per email (max 3/day) ─
            c.execute("""SELECT COUNT(*) as cnt FROM orders
                         WHERE lower(email)=lower(%s)
                         AND submitted_at > NOW() - INTERVAL '24 hours'""", (email,))
            daily_count = (c.fetchone() or {}).get("cnt", 0)
            if daily_count >= 3:
                return jsonify({"success": False,
                    "error": "Maximum 3 orders can be submitted per day from one email."}), 429

            # ── LAYER 13: DUPLICATE ORDER ID CHECK ────────────────────────
            # This is the critical check — case-insensitive, exact match
            c.execute("""SELECT status, email FROM orders
                         WHERE lower(order_id)=lower(%s) LIMIT 1""", (order_id,))
            existing = c.fetchone()
            if existing:
                _log_attempt(conn, ip, email, order_id, was_duplicate=True)
                log.warning("duplicate_order_id order_id=%s new_email=%s existing_email=%s",
                            order_id, mask(email), mask(existing.get("email", "")))
                return jsonify({"success": False,
                    "error": "This Order ID has already been submitted and is being tracked. "
                             "Each order can only earn stars once."}), 409

            # ── LAYER 14: Check same email + different order IDs suspicious ─
            c.execute("""SELECT COUNT(*) as cnt FROM orders
                         WHERE lower(email)=lower(%s)
                         AND submitted_at > NOW() - INTERVAL '7 days'""", (email,))
            week_count = (c.fetchone() or {}).get("cnt", 0)

            # ── LAYER 15: Same IP submitted different emails? ─────────────
            c.execute("""SELECT COUNT(DISTINCT lower(email)) as cnt FROM orders
                         WHERE ip_address=%s
                         AND submitted_at > NOW() - INTERVAL '24 hours'""", (ip,))
            ip_email_count = (c.fetchone() or {}).get("cnt", 0)

            # ── LAYER 16: Fraud score calculation ─────────────────────────
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

            # Check if IP has many failed attempts recently
            c.execute("""SELECT COUNT(*) as cnt FROM submission_attempts
                         WHERE ip_address=%s
                         AND attempted_at > NOW() - INTERVAL '1 hour'
                         AND (was_duplicate OR was_invalid_fmt OR blocked)""", (ip,))
            bad_attempts = (c.fetchone() or {}).get("cnt", 0)
            if bad_attempts >= 5:
                fraud_score += 25
                fraud_reasons.append(f"bad_attempts:{bad_attempts}")

            # Auto-block IP if fraud score is extreme
            if fraud_score >= 80:
                try:
                    c.execute("""INSERT INTO blocked_entities(entity_type, value, reason)
                                 VALUES('ip', %s, %s)
                                 ON CONFLICT(entity_type, value) DO NOTHING""",
                              (ip, f"Auto-blocked: fraud_score={fraud_score} reasons={','.join(fraud_reasons)}"))
                    conn.commit()
                except Exception:
                    pass
                _log_attempt(conn, ip, email, order_id, blocked=True)
                return jsonify({"success": False,
                    "error": "Suspicious activity detected. Access temporarily restricted."}), 403

        # ── LAYER 17: Save files ─────────────────────────────────────────
        pfx = random.randint(10000, 99999)
        op  = save_file(of, f"{pfx}_{secure_filename(of.filename)}")
        rp  = None
        rf  = request.files.get("rating_screenshot")
        if rf and rf.filename and ok_ext(rf.filename):
            rf_bytes = rf.read()
            if 0 < len(rf_bytes) <= MAX_FILE_BYTES:
                rf.seek(0)
                rp = save_file(rf, f"{pfx}r_{secure_filename(rf.filename)}")

        # ── LAYER 18: Insert into DB (atomic) ────────────────────────────
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

        # ── LAYER 19: Log this submission attempt ─────────────────────────
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
    """Log every submission attempt for fraud analysis."""
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO submission_attempts
                         (ip_address, email, order_id, was_duplicate, was_invalid_fmt, blocked)
                         VALUES(%s, %s, %s, %s, %s, %s)""",
                      (ip, email, order_id, was_duplicate, was_invalid_fmt, blocked))
        conn.commit()
    except Exception as ex:
        log.warning("log_attempt_error: %s", ex)


@app.route("/api/admin/run-approvals", methods=["POST"])
@require_admin
def run_approvals():
    """GitHub Actions calls this every day at 3 AM IST. No CSV needed — re-checks DB."""
    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500
    try:
        cfg   = get_config(conn)
        cool  = int(cfg.get("cooling_days","21"))
        minck = int(cfg.get("min_csv_checks_before_approve","3"))
        stale = int(cfg.get("max_csv_staleness_days","5"))
        if cfg.get("auto_approve_enabled","true").lower() != "true":
            return jsonify({"success":True,"approved_count":0,
                            "message":"auto_approve disabled"}),200

        with conn.cursor() as c:
            c.execute("""SELECT order_id,email,token,csv_delivered_at,
                                consecutive_delivered_count,ever_showed_return,csv_last_seen_at
                         FROM orders WHERE status='under_review'""")
            candidates = c.fetchall()

        approved = []
        for o in candidates:
            if not can_approve(o, cool, minck, stale): continue
            with conn.cursor() as c:
                c.execute("""UPDATE orders SET status='approved',
                    approved_at=NOW(), updated_at=NOW()
                  WHERE order_id=%s AND status='under_review' RETURNING order_id""",(o["order_id"],))
                if c.fetchone():
                    audit(c, o["order_id"], "under_review", "approved",
                          f"github_actions:cool={cool}d checks={o['consecutive_delivered_count']}")
                    approved.append({"order_id":o["order_id"],
                                     "email":mask(o["email"]),"token":o["token"]})
            conn.commit()

        log.info("run_approvals: %d approved", len(approved))
        return jsonify({"success":True,"approved_count":len(approved),
                        "approved_orders":approved}),200
    except Exception as e:
        conn.rollback(); log.error("run_approvals: %s",e)
        return jsonify({"success":False,"error":str(e)}),500
    finally:
        conn.close()


# ── ADMIN: UPLOAD CSV ─────────────────────────────────────────────────
@app.route("/api/admin/upload-csv", methods=["POST"])
@require_admin
def upload_csv():
    if "csv_file" not in request.files:
        return jsonify({"success":False,"error":"csv_file required"}),400
    f = request.files["csv_file"]
    if not f.filename.lower().endswith(".csv"):
        return jsonify({"success":False,"error":"Must be .csv"}),400

    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        f.save(tmp.name); tmp_path = tmp.name

    try:
        with conn.cursor() as c:
            c.execute("INSERT INTO csv_sync_log(filename,synced_by) VALUES(%s,'admin_upload') RETURNING id",
                      (f.filename,))
            sid = c.fetchone()["id"]
        conn.commit()

        stats = process_csv(tmp_path, conn, sid)

        with conn.cursor() as c:
            c.execute("""UPDATE csv_sync_log SET
                rows_processed=%s,rows_matched=%s,rows_delivered=%s,
                rows_returned=%s,rows_approved=%s,rows_disputed=%s,rows_skipped=%s
              WHERE id=%s""",
                (stats["rows_processed"],stats["rows_matched"],stats["rows_delivered"],
                 stats["rows_returned"],stats["rows_approved"],stats["rows_disputed"],
                 stats["rows_skipped"],sid))
        conn.commit()
        return jsonify({"success":True,"stats":stats,"sync_log_id":sid}),200
    except Exception as e:
        conn.rollback(); log.error("upload_csv: %s",e)
        return jsonify({"success":False,"error":str(e)}),500
    finally:
        conn.close()
        try: os.unlink(tmp_path)
        except Exception: pass


# ── ADMIN: MARK STALE (called by GitHub Actions) ──────────────────────
@app.route("/api/admin/mark-stale", methods=["POST"])
@require_admin
def mark_stale():
    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500
    try:
        days = int(get_config(conn).get("stale_order_days","45"))
        with conn.cursor() as c:
            c.execute("""UPDATE orders SET status='stale',
                admin_note=COALESCE(admin_note||' | ','')
                          ||'Auto-stale: no CSV match after '||%s||' days',
                updated_at=NOW()
              WHERE status='pending'
                AND submitted_at < NOW()-(%s||' days')::INTERVAL
              RETURNING order_id""", (str(days), str(days)))
            rows = c.fetchall()
        conn.commit()
        return jsonify({"success":True,"marked_count":len(rows)}),200
    except Exception as e:
        conn.rollback()
        return jsonify({"success":False,"error":str(e)}),500
    finally:
        conn.close()


# ── ADMIN: PING (login check — accepts POST) ──────────────────────────
@app.route("/api/admin/ping", methods=["POST"])
@require_admin
def admin_ping():
    """Used by admin.html to verify the secret is correct."""
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


# ── ADMIN: ORDERS ─────────────────────────────────────────────────────
@app.route("/api/admin/orders", methods=["GET"])
@require_admin
def admin_orders():
    sf  = request.args.get("status")
    lim = min(int(request.args.get("limit",100)),500)
    off = int(request.args.get("offset",0))
    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500
    try:
        with conn.cursor() as c:
            if sf:
                c.execute("SELECT * FROM v_admin_orders WHERE status=%s::order_status LIMIT %s OFFSET %s",(sf,lim,off))
            else:
                c.execute("SELECT * FROM v_admin_orders LIMIT %s OFFSET %s",(lim,off))
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
        return jsonify({"success":True,"orders":[dict(r) for r in rows],
                        "counts":dict(counts) if counts else {}}),200
    finally:
        conn.close()


# ── ADMIN: UPDATE ORDER ───────────────────────────────────────────────
@app.route("/api/admin/update-order", methods=["POST"])
@require_admin
def update_order():
    d   = request.get_json(silent=True) or {}
    oid = d.get("order_id","").strip()
    ns  = d.get("status","").strip()
    rr  = d.get("rejection_reason","").strip()
    an  = d.get("admin_note","").strip()
    VALID = {"pending","under_review","approved","rejected","flagged","disputed"}
    if not oid or ns not in VALID:
        return jsonify({"success":False,"error":"Invalid params"}),400
    if ns == "rejected" and not rr:
        return jsonify({"success":False,"error":"rejection_reason required"}),400
    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500
    try:
        with conn.cursor() as c:
            c.execute("SELECT status FROM orders WHERE order_id=%s",(oid,))
            cur = c.fetchone()
            if not cur: return jsonify({"success":False,"error":"Not found"}),404
            c.execute("""UPDATE orders SET
                status=%s::order_status,
                rejection_reason=COALESCE(NULLIF(%s,''),rejection_reason),
                admin_note=COALESCE(NULLIF(%s,''),admin_note),
                approved_at=CASE WHEN %s='approved' THEN NOW() ELSE approved_at END,
                rejected_at=CASE WHEN %s='rejected' THEN NOW() ELSE rejected_at END,
                updated_at=NOW()
              WHERE order_id=%s RETURNING order_id,status,email""",
                (ns,rr,an,ns,ns,oid))
            upd = c.fetchone()
            audit(c, oid, cur["status"], ns, f"admin_override:{an or rr}")
        conn.commit()
        return jsonify({"success":True,"order":dict(upd)}),200
    except Exception as e:
        conn.rollback()
        return jsonify({"success":False,"error":str(e)}),500
    finally:
        conn.close()


# ── ADMIN: CONFIG ─────────────────────────────────────────────────────
@app.route("/api/admin/config", methods=["GET"])
@require_admin
def get_cfg():
    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500
    try:
        with conn.cursor() as c:
            c.execute("SELECT key,value,description,updated_at FROM system_config ORDER BY key")
            return jsonify({"success":True,"config":[dict(r) for r in c.fetchall()]}),200
    finally:
        conn.close()

@app.route("/api/admin/config", methods=["POST"])
@require_admin
def set_cfg():
    d = request.get_json(silent=True) or {}
    k = d.get("key","").strip(); v = d.get("value","").strip()
    OK = {"cooling_days","min_csv_checks_before_approve",
          "max_csv_staleness_days","auto_approve_enabled","stale_order_days"}
    if k not in OK: return jsonify({"success":False,"error":f"Not editable: {k}"}),400
    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500
    try:
        with conn.cursor() as c:
            c.execute("UPDATE system_config SET value=%s,updated_at=NOW() WHERE key=%s RETURNING key,value",(v,k))
            upd = c.fetchone()
        conn.commit()
        if not upd: return jsonify({"success":False,"error":"Key not found"}),404
        return jsonify({"success":True,"config":dict(upd)}),200
    except Exception as e:
        conn.rollback(); return jsonify({"success":False,"error":str(e)}),500
    finally:
        conn.close()


# ── ADMIN: SYNC LOGS ──────────────────────────────────────────────────
@app.route("/api/admin/sync-logs", methods=["GET"])
@require_admin
def sync_logs():
    conn = get_db()
    if not conn: return jsonify({"success":False,"error":"Database unavailable"}),500
    try:
        with conn.cursor() as c:
            c.execute("SELECT * FROM csv_sync_log ORDER BY synced_at DESC LIMIT 30")
            return jsonify({"success":True,"sync_logs":[dict(r) for r in c.fetchall()]}),200
    finally:
        conn.close()



# ── API: GET STARS (check-stars page) ────────────────────────────────
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
            # Get user record
            c.execute("""
                SELECT total_stars, submission_count, created_at
                FROM users WHERE lower(email)=lower(%s)
            """, (email,))
            user = c.fetchone()

            if not user:
                return jsonify({"success": True, "found": False}), 200

            # Get order breakdown by status
            c.execute("""
                SELECT
                  COUNT(*) FILTER(WHERE status='approved')      AS approved,
                  COUNT(*) FILTER(WHERE status='pending')       AS pending,
                  COUNT(*) FILTER(WHERE status='under_review')  AS under_review,
                  COUNT(*) FILTER(WHERE status='rejected')      AS rejected,
                  COUNT(*) FILTER(WHERE status='disputed')      AS disputed,
                  COUNT(*) FILTER(WHERE status='stale')         AS stale,
                  COUNT(*)                                      AS total
                FROM orders WHERE lower(email)=lower(%s)
            """, (email,))
            counts = c.fetchone() or {}

            # Get recent orders list (last 10)
            c.execute("""
                SELECT order_id, status, submitted_at, approved_at,
                       token, rejection_reason
                FROM orders
                WHERE lower(email)=lower(%s)
                ORDER BY submitted_at DESC LIMIT 10
            """, (email,))
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
                    "order_id":   o["order_id"],
                    "status":     o["status"],
                    "submitted":  o["submitted_at"].isoformat() if o.get("submitted_at") else None,
                    "approved":   o["approved_at"].isoformat()  if o.get("approved_at")  else None,
                    "token":      o["token"],
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


# ── WAKE: pre-warm endpoint (called before submit) ───────────────────
@app.route("/api/wake", methods=["GET"])
def wake():
    """Frontend calls this on page load to pre-warm DB connection."""
    conn = get_db()
    if conn:
        conn.close()
        return jsonify({"status": "ready"}), 200
    return jsonify({"status": "starting"}), 503


# ── HEALTH (UptimeRobot pings this every 5 min) ───────────────────────
@app.route("/health")
@app.route("/api/health")
def health():
    if not DATABASE_URL:
        return jsonify({"status":"unhealthy","error":"DATABASE_URL missing"}),500
    conn = get_db()
    if conn:
        conn.close()
        return jsonify({"status":"healthy","database":"connected",
                        "automation":"github_actions","project":"fqsvksjhphutjnkvgnmk"}),200
    return jsonify({"status":"unhealthy","database":"disconnected"}),500


# ── ERROR HANDLERS ────────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(_):
    if request.path.startswith("/api/"):
        return jsonify({"success":False,"error":"File too large (max 5 MB)"}),413
    return "File too large",413

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"success":False,"error":"Not found"}),404
    return "Not Found",404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)), debug=False)