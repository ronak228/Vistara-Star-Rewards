"""
automation/github_trigger.py
==============================
Runs inside GitHub Actions every day at 3 AM IST (free, 2000 min/month).
Calls your Render app to run approvals and clean up stale orders.
No Playwright. No paid scheduler. Zero cost.

Required GitHub secrets (repo Settings → Secrets → Actions):
  APP_URL       = https://your-app.onrender.com
  ADMIN_SECRET  = your admin secret string
"""

import os, sys, requests

APP_URL      = os.environ.get("APP_URL", "").rstrip("/")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")

if not APP_URL or not ADMIN_SECRET:
    print("ERROR: APP_URL and ADMIN_SECRET must be set as GitHub secrets.")
    sys.exit(1)

HDR = {"X-Admin-Secret": ADMIN_SECRET, "Content-Type": "application/json"}

def call(path, method="POST"):
    url = f"{APP_URL}{path}"
    try:
        r = (requests.get if method=="GET" else requests.post)(
            url, headers=HDR, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.Timeout:
        return {"success": False, "error": "timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print(f"=== Vistara Daily Run — {APP_URL} ===\n")
    ok = True

    # 1. Wake Render (free plan may be sleeping)
    print("[1/3] Health check...")
    h = call("/health", "GET")
    print(f"      {h.get('status','unknown')} | db={h.get('database','?')}")

    # 2. Run approval gate on all under_review orders
    print("\n[2/3] Running approvals...")
    r = call("/api/admin/run-approvals")
    if r.get("success"):
        n = r.get("approved_count", 0)
        print(f"      OK — {n} order(s) approved")
        for o in r.get("approved_orders", []):
            print(f"        ✓ {o['order_id']} | {o['email']} | {o['token']}")
    else:
        print(f"      FAILED: {r.get('error')}")
        ok = False

    # 3. Mark old unmatched orders as stale
    print("\n[3/3] Marking stale orders...")
    s = call("/api/admin/mark-stale")
    if s.get("success"):
        print(f"      OK — {s.get('marked_count',0)} stale order(s) flagged")
    else:
        print(f"      WARNING: {s.get('error','unavailable')}")

    print("\n=== Done ===")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()