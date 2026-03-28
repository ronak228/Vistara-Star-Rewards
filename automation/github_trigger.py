"""
automation/github_trigger.py
Runs inside GitHub Actions every day at 3 AM IST.
Calls Vercel app to auto-approve eligible orders and reject stale/fake ones.
"""

import os, sys, requests, time

APP_URL      = os.environ.get("APP_URL", "").rstrip("/")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")

if not APP_URL:
    print("ERROR: APP_URL secret not set in GitHub.")
    print("Go to: repo Settings → Secrets and variables → Actions → New repository secret")
    print("Add: APP_URL = https://your-project.vercel.app")
    sys.exit(1)

if not ADMIN_SECRET:
    print("ERROR: ADMIN_SECRET secret not set in GitHub.")
    print("Go to: repo Settings → Secrets and variables → Actions → New repository secret")
    print("Add: ADMIN_SECRET = your admin password from Vercel env vars")
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

    # 1. Health check — Vercel spins up instantly, no warm-up needed
    print("[1/3] Health check...")
    h = call("/health", "GET")
    status = h.get("status", "unknown")
    db     = h.get("database", "unknown")
    print(f"      Status: {status} | DB: {db}")
    if status != "healthy":
        print("      WARNING: Server unhealthy but continuing...")

    # 2. Run approvals — auto-approve under_review orders past 15 days
    # This runs every day so even if you forget to upload CSV on Sunday,
    # verified orders will still be approved on time automatically.
    print("\n[2/3] Running approvals...")
    r = call("/api/admin/run-approvals")
    if r.get("success"):
        n = r.get("approved_count", 0)
        s = r.get("stale_rejected", 0)
        print(f"      OK — {n} order(s) approved, {s} stale/fake rejected")
        if n == 0:
            print("      (No orders ready yet — normal if < 15 days since submission)")
    else:
        err = r.get("error", "unknown")
        print(f"      WARNING: {err}")

    # 3. Mark stale orders — reject fake/unverified orders older than 20 days
    print("\n[3/3] Marking stale orders...")
    s = call("/api/admin/mark-stale")
    if s.get("success"):
        n = s.get("marked_count", 0)
        print(f"      OK — {n} stale order(s) rejected")
    else:
        print(f"      WARNING: {s.get('error', 'unknown')}")

    print("\n=== Done ===")
    sys.exit(0)  # Always exit 0 unless secrets missing

if __name__ == "__main__":
    main()