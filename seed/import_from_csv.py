import csv, sqlite3, os

DB_PATH = os.path.join("..", "backend", "surething.db")

def import_accounts():
    with open("accounts.csv", newline="", encoding="utf-8") as f:
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
    with open("categories.csv", newline="", encoding="utf-8") as f:
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
    with open("requests.csv", newline="", encoding="utf-8") as f:
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
    import_accounts()
    import_categories()
    import_requests()
    print("🎉 All CSV data imported into SQLite.")
