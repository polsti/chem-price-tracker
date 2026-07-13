from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import get_latest_all, get_history

app = FastAPI(title="Chemical Price Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Chemical Price Tracker API"}


@app.get("/chemicals")
def chemicals_latest():
    """Latest price for all 8 chemicals, including their IDs and names."""
    rows = get_latest_all()
    if not rows:
        raise HTTPException(status_code=404, detail="No data in database yet")
    return rows


@app.get("/chemicals/{chemical_id}/history")
def chemical_history(chemical_id: str, days: int = 30):
    """Full price history for one chemical. Default: last 30 days."""
    rows = get_history(chemical_id, limit=days)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for chemical_id={chemical_id}")
    return rows


@app.get("/chemicals/{chemical_id}/latest")
def chemical_latest(chemical_id: str):
    """Most recent price row for one chemical."""
    rows = get_history(chemical_id, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No data found for chemical_id={chemical_id}")
    return rows[0]
