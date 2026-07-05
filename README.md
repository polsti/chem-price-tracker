# Chemical Price Tracker

Internal tool for tracking industrial chemical prices from sci99.com.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Project phases

- Phase 2 (current) — Playwright scraper for acetone (oldId=449)
- Phase 3 — extend to all 8 chemicals + SQLite storage
- Phase 4 — daily cron automation
- Phase 5 — FastAPI backend
- Phase 6 — dashboard (tables, charts, trend/prediction)
- Phase 7 — monthly Excel/PDF reports
