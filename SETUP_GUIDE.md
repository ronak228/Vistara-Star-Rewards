# Vistara Rewards — Final Setup Guide
# Total monthly cost: ₹0

## What's fixed in this version
- CSS loading fixed: file is now at static/css/style.css (templates were referencing css/ subfolder)
- Supabase database fully migrated via connector (live at fqsvksjhphutjnkvgnmk, ap-south-1)
- No APScheduler, no Playwright, no paid workers
- GitHub Actions runs daily automation for free

---

## Your Supabase project (already done via connector)
Project: vistara-loyalty
ID: fqsvksjhphutjnkvgnmk
Region: ap-south-1 (Mumbai)
Status: ACTIVE_HEALTHY

All tables, triggers, views, and indexes are already applied.
The system_config table is seeded with default values.

---

## Step 1: Render environment variables

In Render dashboard → your web service → Environment:

DATABASE_URL     = postgresql://postgres.[password]@db.fqsvksjhphutjnkvgnmk.supabase.co:5432/postgres
ADMIN_SECRET     = [pick a strong random string, keep it secret]
DB_SSLMODE       = require

# For screenshot storage (Cloudflare R2, free 10 GB):
R2_ENABLED       = true
R2_ACCOUNT_ID    = [from Cloudflare R2 dashboard]
R2_ACCESS_KEY    = [R2 API token access key]
R2_SECRET_KEY    = [R2 API token secret key]
R2_BUCKET_NAME   = vistara-screenshots

Get DATABASE_URL from: Supabase → Project Settings → Database → Connection string (URI)

---

## Step 2: Render build & start commands

Build:  pip install -r requirements.txt
Start:  gunicorn app:app --workers 1 --timeout 60 --bind 0.0.0.0:$PORT

---

## Step 3: UptimeRobot (keeps Render free plan awake)

1. uptimerobot.com → New Monitor
2. Type: HTTP(s)
3. URL: https://your-app.onrender.com/health
4. Interval: 5 minutes

This pings /health every 5 minutes so Render never sleeps.

---

## Step 4: GitHub Actions (daily automation, free)

1. Push this entire folder to a GitHub repo (private is fine)
2. GitHub repo → Settings → Secrets → Actions → New:
   APP_URL      = https://your-app.onrender.com
   ADMIN_SECRET = [same string as Render env var]
3. Go to Actions tab → "Vistara Daily Order Processor" → Run workflow (test it once)

The workflow runs every day at 3:00 AM IST automatically.
It calls /api/admin/run-approvals to approve eligible orders.
Uses ~1 minute/day = ~30 minutes/month (free tier gives 2000 min/month).

---

## Daily workflow (what you do each day, takes 3 minutes)

1. Open Meesho seller panel → Orders → Export CSV (last 45 days)
2. Go to https://your-app.onrender.com/admin
3. Enter ADMIN_SECRET
4. Dashboard → Upload CSV → select file → click Upload & Process

That's it. Approvals run automatically at 3 AM IST even if you skip the CSV.
The more consistently you upload, the more accurately the fraud gate catches returns.

---

## How approval works (the fraud gate)

Every order under review must pass ALL 4 conditions before getting approved:

1. ever_showed_return = FALSE
   Once a CSV shows Returned/RTO, this is permanently TRUE — order can never be approved.

2. Days since delivery >= 21
   Covers: 7-day return window + 10 days courier transit back + 4 days CSV lag.

3. consecutive_delivered_count >= 3
   Must appear as "Delivered" in at least 3 separate CSV uploads in a row.
   This count resets to 0 the moment any CSV shows a return.

4. csv_last_seen_at within 5 days
   Approval only fires when you have fresh data — prevents approving on stale CSV.

If all 4 pass → status = approved → star added automatically (DB trigger).

---

## Admin panel pages

/admin  — main admin dashboard
  Dashboard tab: order counts, ready-to-approve list, CSV upload
  Orders tab:    view/filter all orders, manual approve/reject
  Sync Logs tab: history of every CSV upload
  Config tab:    adjust settings without redeploy

Config values you can change live:
  cooling_days                  = 21  (increase if catching late returns)
  min_csv_checks_before_approve = 3   (increase for stricter fraud prevention)
  max_csv_staleness_days        = 5   (increase if uploading CSV every 3-4 days)
  auto_approve_enabled          = true (set false to pause all auto-approvals)
  stale_order_days              = 45  (pending orders with no CSV match after this)

---

## File structure

vistara_final/
├── app.py                          ← Flask backend (all logic here)
├── requirements.txt
├── runtime.txt
├── templates/
│   ├── index.html                  ← Main page (QR landing page)
│   ├── check-stars.html            ← Stars lookup page
│   └── admin.html                  ← Admin dashboard
├── static/
│   ├── css/
│   │   └── style.css               ← CSS (was missing this folder — now fixed)
│   └── js/
│       ├── main.js
│       ├── check-stars.js
│       └── translations.js
└── automation/
    ├── github_trigger.py           ← Called by GitHub Actions daily
    └── .github/workflows/
        └── daily_processor.yml     ← GitHub Actions cron definition
