# seed/import_from_csv.py
import csv, sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent          # .../seed
REPO = BASE.parent                               # 레포 루트
DB_PATH = REPO / "backend" / "surething.db"     # .../backend/surething.db

ACCOUNTS_CSV   = BASE / "accounts.csv"
CATEGORIES_CSV = BASE / "categories.csv"
REQUESTS_CSV   = BASE / "requests.csv"

def import_accounts():
    with ACCOUNTS_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for row in reader:
            cur.execute("""
                INSERT OR IGNORE INTO accounts (id,email,name,role,is_active)
                VALUES (?,?,?,?,?)
            """, (row["id"], row["email"], row["name"], row["role"], row["is_active"]))
        conn.commit(); conn.close()
    print("✅ Accounts imported.")

def import_categories():
    with CATEGORIES_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for row in reader:
            cur.execute("""
                INSERT OR IGNORE INTO categories (id,name,description)
                VALUES (?,?,?)
            """, (row["id"], row["name"], row["description"]))
        conn.commit(); conn.close()
    print("✅ Categories imported.")

def import_requests():
    with REQUESTS_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for row in reader:
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
    print("✅ Requests imported.")

if __name__ == "__main__":
    # 파일 존재 체크(오타·대소문자 확인)
    assert ACCOUNTS_CSV.exists(),   f"Missing: {ACCOUNTS_CSV}"
    assert CATEGORIES_CSV.exists(), f"Missing: {CATEGORIES_CSV}"
    assert REQUESTS_CSV.exists(),   f"Missing: {REQUESTS_CSV}"
    assert DB_PATH.exists(),        f"Missing DB: {DB_PATH} (run init_db first)"

    import_accounts()
    import_categories()
    import_requests()
    print(f"🎉 All CSV imported into {DB_PATH}")
