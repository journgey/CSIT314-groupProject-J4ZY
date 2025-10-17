# seed/import_from_json.py
import json, sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent          # .../seed
REPO = BASE.parent                              # 레포 루트
DB_PATH = REPO / "backend" / "surething.db"     # .../backend/surething.db
DATA_DIR = REPO / "seed"            # JSON 저장 폴더

ACCOUNTS_JSON   = DATA_DIR / "accounts.json"
CATEGORIES_JSON = DATA_DIR / "categories.json"
REQUESTS_JSON   = DATA_DIR / "requests.json"


def import_accounts():
    with ACCOUNTS_JSON.open(encoding="utf-8") as f:
        rows = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for row in rows:
        cur.execute("""
            INSERT OR IGNORE INTO accounts (id,email,name,role,is_active)
            VALUES (?,?,?,?,?)
        """, (row["id"], row["email"], row["name"], row["role"], row["is_active"]))
    conn.commit(); conn.close()
    print(f"✅ Imported {len(rows)} accounts from {ACCOUNTS_JSON.name}")


def import_categories():
    with CATEGORIES_JSON.open(encoding="utf-8") as f:
        rows = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for row in rows:
        cur.execute("""
            INSERT OR IGNORE INTO categories (id,name,description)
            VALUES (?,?,?)
        """, (row["id"], row["name"], row["description"]))
    conn.commit(); conn.close()
    print(f"✅ Imported {len(rows)} categories from {CATEGORIES_JSON.name}")


def import_requests():
    with REQUESTS_JSON.open(encoding="utf-8") as f:
        rows = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for row in rows:
        cur.execute("""
            INSERT OR IGNORE INTO requests
            (id,pin_account_id,title,description,category_id,status)
            VALUES (?,?,?,?,?,?)
        """, (
            row["id"],
            row["pin_account_id"],
            row["title"],
            row["description"],
            row["category_id"],
            row["status"]
        ))
    conn.commit(); conn.close()
    print(f"✅ Imported {len(rows)} requests from {REQUESTS_JSON.name}")


if __name__ == "__main__":
    # 파일 확인
    assert DB_PATH.exists(), f"Missing DB: {DB_PATH} (run init_db first)"
    assert ACCOUNTS_JSON.exists(), f"Missing {ACCOUNTS_JSON}"
    assert CATEGORIES_JSON.exists(), f"Missing {CATEGORIES_JSON}"
    assert REQUESTS_JSON.exists(), f"Missing {REQUESTS_JSON}"

    import_accounts()
    import_categories()
    import_requests()
    print(f"🎉 All JSON imported into {DB_PATH}")
