# backend/db_session.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from flask import g

BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR / "surething.db"

def get_db():
    """Return a per-request SQLite connection stored on Flask 'g'."""
    if "db" not in g:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db

def close_db(_e=None):
    """Close the connection at the end of the request/app context."""
    db = g.pop("db", None)
    if db is not None:
        db.close()
