# backend/repository/db.py
import sqlite3
from pathlib import Path

# DB 파일 경로: <repo>/backend/surething.db
DB_PATH = Path(__file__).resolve().parent.parent / "surething.db"

def get_conn():
    """
    SQLite 연결을 반환. row_factory를 Row로 설정해 dict처럼 접근 가능.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    스키마 생성(존재하면 유지). 외래키 활성화 및 합리적인 제약 포함.
    """
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
      FOREIGN KEY(category_id)  REFERENCES categories(id) ON DELETE SET NULL
    );

    -- updated_at 자동 업데이트 트리거 (옵션)
    CREATE TRIGGER IF NOT EXISTS trg_requests_updated_at
    AFTER UPDATE ON requests
    FOR EACH ROW
    BEGIN
      UPDATE requests SET updated_at = datetime('now') WHERE id = NEW.id;
    END;
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # 단독 실행 시 스키마 초기화
    init_db()
    print(f"✅ Database initialized at {DB_PATH}")
