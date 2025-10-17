import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "surething.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS accounts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      name TEXT,
      role TEXT CHECK(role IN ('PIN','CSR','ADMIN')) NOT NULL DEFAULT 'PIN',
      is_active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS categories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT UNIQUE NOT NULL,
      description TEXT
    );

    CREATE TABLE IF NOT EXISTS requests (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      pin_account_id INTEGER NOT NULL,
      title TEXT NOT NULL,
      description TEXT,
      category_id INTEGER,
      status TEXT CHECK(status IN ('OPEN','IN_PROGRESS','CLOSED')) NOT NULL DEFAULT 'OPEN',
      created_at DATETIME DEFAULT (datetime('now')),
      updated_at DATETIME DEFAULT (datetime('now')),
      FOREIGN KEY(pin_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
      FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    conn.close()
