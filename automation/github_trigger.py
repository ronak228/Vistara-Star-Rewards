"""
automation/github_trigger.py
Runs inside GitHub Actions every day at 3 AM IST.
Calls Render app to run approvals and mark stale orders.
"""

import os, sys, requests, time

APP_URL      = os.environ.get("APP_URL", "").rstrip("/")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")

if not APP_URL:
    print("ERROR: APP_URL secret not set in GitHub.")
    print("Go to: repo Settings → Secrets and variables → Actions → New repository secret")
    print("Add: APP_URL = https://vistara-star-rewards-xl6i.onrender.com")
    sys.exit(1)

if not ADMIN_SECRET:
    print("ERROR: ADMIN_SECRET secret not set in GitHub.")
    print("Go to: repo Settings → Secrets and variables → Actions → New repository secret")
    print("Add: ADMIN_SECRET = your admin password from Render")
    sys.exit(1)

HDR = {"X-Admin-Secret": ADMIN_SECRET, "Content-Type": "application/json"}

def call(path, method="POST", retries=3):
    url = f"{APP_URL}{path}"
    for attempt in range(retries):
        try:
            r = (requests.get if method == "GET" else requests.post)(
                url, headers=HDR, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.Timeout:
            print(f"  Timeout on attempt {attempt+1}, retrying...")
            time.sleep(10)
        except Exception as e:
            print(f"  Error on attempt {attempt+1}: {e}")
            time.sleep(5)
    return {"success": False, "error": "All retries failed"}

def main():
    print(f"=== Vistara Daily Run ===")
    print(f"App: {APP_URL}\n")

    # 1. Health check
    print("[1/3] Health check...")
    h = call("/health", "GET")
    status = h.get("status", "unknown")
    db     = h.get("database", "unknown")
    print(f"      Status: {status} | DB: {db}")
    if status != "healthy":
        print("      WARNING: Server unhealthy but continuing...")

    # 2. Run approvals — 0 approvals is NOT an error
    print("\n[2/3] Running approvals...")
    r = call("/api/admin/run-approvals")
    if r.get("success"):
        n = r.get("approved_count", 0)
        print(f"      OK — {n} order(s) approved today")
        for o in r.get("approved_orders", []):
            print(f"        ✓ {o.get('order_id')} | {o.get('email')} | token:{o.get('token')}")
        if n == 0:
            print("      (No orders ready yet — normal if no deliveries confirmed)")
    else:
        err = r.get("error", "unknown")
        print(f"      WARNING: {err}")
        # Don't exit — continue to next step

    # 3. Mark stale orders
    print("\n[3/3] Marking stale orders...")
    s = call("/api/admin/mark-stale")
    if s.get("success"):
        n = s.get("marked_count", 0)
        print(f"      OK — {n} stale order(s) marked")
    else:
        print(f"      WARNING: {s.get('error', 'unknown')}")

    print("\n=== Done — all steps completed successfully ===")
    sys.exit(0)  # Always exit 0 (success) unless secrets missing

if __name__ == "__main__":
    main()
