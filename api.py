from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from db import get_latest_all, get_history, get_monthly_summary, get_client

app = FastAPI(title="Chemical Price Tracker API")


def require_login(authorization: str = Header(None)):
    """
    Runs before any route that depends on it. Reads the "Authorization"
    header the dashboard sends with each request (format: "Bearer <token>"),
    and asks Supabase to confirm that token really came from a logged-in
    user and hasn't expired. Raises a 401 error (blocking the request)
    if anything about that isn't true.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing login token")

    token = authorization.removeprefix("Bearer ")
    try:
        user = get_client().auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired login token")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired login token")

    return user

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",              # local dev (npm run dev)
        "https://chem-price-tracker.vercel.app",  # hosted dashboard
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Chemical Price Tracker API"}


@app.get("/chemicals")
def chemicals_latest(user = Depends(require_login)):
    """Latest price for all 8 chemicals, including their IDs and names."""
    rows = get_latest_all()
    if not rows:
        raise HTTPException(status_code=404, detail="No data in database yet")
    return rows


@app.get("/chemicals/{chemical_id}/history")
def chemical_history(chemical_id: str, days: int = 30, user = Depends(require_login)):
    """Full price history for one chemical. Default: last 30 days."""
    rows = get_history(chemical_id, limit=days)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for chemical_id={chemical_id}")
    return rows


@app.get("/chemicals/{chemical_id}/latest")
def chemical_latest(chemical_id: str, user = Depends(require_login)):
    """Most recent price row for one chemical."""
    rows = get_history(chemical_id, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for chemical_id={chemical_id}")
    return rows[0]


@app.get("/export/summary")
def export_summary(year: int = None, month: int = None, user = Depends(require_login)):
    """Monthly summary for all chemicals — min, max, avg, % change."""
    now = datetime.now()
    year  = year  or now.year
    month = month or now.month
    rows = get_monthly_summary(year, month)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data for {year}-{month:02d}")
    return {"year": year, "month": month, "chemicals": rows}
