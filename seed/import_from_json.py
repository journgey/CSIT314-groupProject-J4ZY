
"""
import_from_json.py

Purpose:
  - Optionally create/initialize a fresh SQLite database from a schema SQL file.
  - Then load seed JSON files into the database according to the provided schema.

Key features:
  - --schema PATH: Apply schema SQL to create a NEW DB (with --init).
  - --init: Create a new DB from --schema. Use --force to overwrite an existing DB.
  - --db PATH: Target DB path (default: ../backend/surething.db relative to this script).
  - --data DIR: Seed JSON directory (default: current script directory).
  - Idempotent INSERTs via INSERT OR IGNORE.
  - `volunteers` serialized as JSON string so JSON_ARRAY_LENGTH() works in CHECK constraints.
  - If `created_at` is missing for a request, DB DEFAULT is used.

Usage examples:
  # 1) Create a fresh DB from schema.sql and import all JSON
  python import_from_json.py --schema ../schema.sql --init --force

  # 2) Import into an existing DB (no schema changes)
  python import_from_json.py --db ../backend/surething.db --data ./seed

  # 3) Custom paths
  python import_from_json.py --db ./out/my.db --data ./seed --schema ./schema.sql --init --force
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# ---------- CLI ----------
def parse_args():
    p = argparse.ArgumentParser(description="Initialize SQLite DB (optional) and import JSON seeds.")
    p.add_argument("--db", type=Path, default=None, help="Path to SQLite DB (default: ../backend/surething.db)")
    p.add_argument("--data", type=Path, default=None, help="Directory containing JSON seeds (default: script dir)")
    p.add_argument("--schema", type=Path, default=None, help="Path to schema SQL file (used with --init)")
    p.add_argument("--init", action="store_true", help="Create a NEW DB from --schema")
    p.add_argument("--force", action="store_true", help="Overwrite DB file when used with --init")
    return p.parse_args()

# ---------- Paths ----------
def resolve_paths(args):
    base = Path(__file__).resolve().parent  # script directory (default data dir)
    repo = base.parent                      # repo root (default db dir)

    db_path = args.db if args.db else (repo / "backend" / "surething.db")
    data_dir = args.data if args.data else base

    return base, repo, db_path, data_dir

# ---------- DB helpers ----------
def create_new_db(db_path: Path, schema_sql_path: Path, force: bool) -> None:
    if not schema_sql_path or not schema_sql_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_sql_path}")

    if db_path.exists():
        if not force:
            raise FileExistsError(f"DB already exists: {db_path}. Use --force to overwrite.")
        db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    sql = schema_sql_path.read_text(encoding="utf-8")
    # Ensure PRAGMA foreign_keys is on after schema creation
    with sqlite3.connect(db_path) as conn:
        conn.executescript(sql)
        conn.execute("PRAGMA foreign_keys = ON;")
    print(f"🆕 Created new DB from schema: {db_path}")

def connect_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"DB does not exist: {db_path}. Use --init with --schema to create a new DB.")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def insert_many(conn: sqlite3.Connection, sql: str, rows: List[Tuple[Any, ...]], label: str) -> int:
    if not rows:
        print(f"⏭️  {label}: no rows")
        return 0
    cur = conn.cursor()
    cur.executemany(sql, rows)
    conn.commit()
    print(f"✅ {label}: inserted (or ignored) {len(rows)} rows")
    return len(rows)

# ---------- JSON loader ----------
def load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        print(f"⚠️  Missing file: {path.name} (skipping)")
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError(f"{path.name} must contain a JSON array of objects")
    return data

# ---------- Importers ----------
def import_companies(conn: sqlite3.Connection, path: Path) -> int:
    rows = load_json(path)
    payload = [(r.get("id"), r["name"]) for r in rows]
    sql = "INSERT OR IGNORE INTO companies (id, name) VALUES (?, ?);"
    return insert_many(conn, sql, payload, "companies")

def import_accounts(conn: sqlite3.Connection, path: Path) -> int:
    rows = load_json(path)
    payload = [(
        r.get("id"),
        r["email"],
        r["password"],
        r.get("name"),
        r.get("phone"),
        r["role"],
        r.get("status", "active"),
        r.get("company_id")
    ) for r in rows]
    sql = (
        "INSERT OR IGNORE INTO accounts "
        "(id, email, password, name, phone, role, status, company_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    )
    return insert_many(conn, sql, payload, "accounts")

def import_volunteers(conn: sqlite3.Connection, path: Path) -> int:
    rows = load_json(path)
    payload = [(
        r.get("id"),
        r.get("name"),
        r.get("email"),
        r.get("phone"),
        r.get("company_id")
    ) for r in rows]
    sql = (
        "INSERT OR IGNORE INTO volunteers "
        "(id, name, email, phone, company_id) VALUES (?, ?, ?, ?, ?);"
    )
    return insert_many(conn, sql, payload, "volunteers")

def import_categories(conn: sqlite3.Connection, path: Path) -> int:
    rows = load_json(path)
    payload = [(r.get("id"), r["name"], r.get("description")) for r in rows]
    sql = "INSERT OR IGNORE INTO categories (id, name, description) VALUES (?, ?, ?);"
    return insert_many(conn, sql, payload, "categories")

def import_regions(conn: sqlite3.Connection, path: Path) -> int:
    rows = load_json(path)
    payload = [(r.get("id"), r["name"]) for r in rows]
    sql = "INSERT OR IGNORE INTO regions (id, name) VALUES (?, ?);"
    return insert_many(conn, sql, payload, "regions")

def import_districts(conn: sqlite3.Connection, path: Path) -> int:
    rows = load_json(path)
    payload = [(r.get("id"), r["region_id"], r["name"]) for r in rows]
    sql = "INSERT OR IGNORE INTO districts (id, region_id, name) VALUES (?, ?, ?);"
    return insert_many(conn, sql, payload, "districts")

def normalize_volunteers(value: Any) -> str:
    """
    Ensure volunteers are serialized as a JSON array string.
    Accepts: list[int], list[str], comma-separated string, None.
    Returns: JSON string (e.g., "[]", "[1,2]")
    """
    if value is None:
        return "[]"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        s = value.strip()
        if s == "":
            return "[]"
        # Try JSON parse first
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return json.dumps(parsed, ensure_ascii=False)
        except Exception:
            pass
        # Fallback: comma-separated
        parts = [p.strip() for p in s.split(",") if p.strip()]
        ints = []
        for p in parts:
            try:
                ints.append(int(p))
            except Exception:
                continue
        return json.dumps(ints, ensure_ascii=False)
    return "[]"

def import_requests(conn: sqlite3.Connection, path: Path) -> int:
    rows = load_json(path)
    payload_with_created = []
    payload_no_created = []

    for r in rows:
        volunteers_json = normalize_volunteers(r.get("volunteers"))
        base = (
            r.get("id"),
            r["pin_id"],
            r.get("csr_id"),
            r["category_id"],
            r["district_id"],
            r["title"],
            r.get("description"),
            r["status"],
            r.get("start_at"),
            r.get("end_at"),
            volunteers_json
        )
        if r.get("created_at") is not None:
            payload_with_created.append(base + (r["created_at"],))
        else:
            payload_no_created.append(base)

    sql_with_created = (
        "INSERT OR IGNORE INTO requests "
        "(id, pin_id, csr_id, category_id, district_id, title, description, status, start_at, end_at, volunteers, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
    )
    sql_no_created = (
        "INSERT OR IGNORE INTO requests "
        "(id, pin_id, csr_id, category_id, district_id, title, description, status, start_at, end_at, volunteers) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
    )

    cur = conn.cursor()
    if payload_with_created:
        cur.executemany(sql_with_created, payload_with_created)
    if payload_no_created:
        cur.executemany(sql_no_created, payload_no_created)
    conn.commit()
    print(f"✅ requests: inserted (or ignored) {len(rows)} rows")
    return len(rows)

# ---------- Orchestration ----------
def main():
    args = parse_args()
    base, repo, db_path, data_dir = resolve_paths(args)

    # Initialize a NEW DB if requested
    if args.init:
        if not args.schema:
            print("❌ --init requires --schema PATH", file=sys.stderr)
            sys.exit(2)
        create_new_db(db_path, args.schema, force=args.force)

    # Connect to target DB
    conn = connect_db(db_path)
    try:
        # Import order matters (parents first)
        import_companies(conn, data_dir / "companies.json")
        import_accounts(conn, data_dir / "accounts.json")
        import_volunteers(conn, data_dir / "volunteers.json")
        import_categories(conn, data_dir / "categories.json")
        import_regions(conn, data_dir / "regions.json")
        import_districts(conn, data_dir / "districts.json")
        import_requests(conn, data_dir / "requests.json")
    finally:
        conn.close()

    print(f"🎉 Done. Imported JSON seeds into {db_path}")

# ---------- Non-CLI entry point for external use ----------
def run_with_existing_conn(conn, data_dir):
    """
    Import all JSON seed files into an EXISTING database connection.
    Used by Flask app during startup (no new connection opened).
    """
    print("🌱 Running seeder with existing connection...")
    # Import order matters (parents first)
    import_companies(conn, data_dir / "companies.json")
    import_accounts(conn, data_dir / "accounts.json")
    import_volunteers(conn, data_dir / "volunteers.json")
    import_categories(conn, data_dir / "categories.json")
    import_regions(conn, data_dir / "regions.json")
    import_districts(conn, data_dir / "districts.json")
    import_requests(conn, data_dir / "requests.json")
    conn.commit()
    print("✅ JSON seeding completed via existing connection.")

if __name__ == "__main__":
    main()
