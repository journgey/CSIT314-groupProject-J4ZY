class AccountsRepository:

    def __init__(self, conn):
        self.conn = conn
    
    # Create
    def create_account(self, email, password, name, phone, role, status, company_id=None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO accounts (email, password, name, phone, role, status, company_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (email, password, name, phone, role, status, company_id)
        )
        self.conn.commit()
        account_id = cur.lastrowid
        return {"id": account_id, "email": email, "password": password, "name": name, "phone": phone, "role": role, "status": status, "company_id": company_id }


    # Retrieve one
    def get_account_by_id(self, account_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE id = ? ORDER BY id ASC", (account_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    
    def get_account_by_email(self, email):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE email = ? ORDER BY id ASC", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


    # Retrieve all
    def list_accounts(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM accounts ORDER BY id ASC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    

    # Update
    def update_account(self, account_id, **updates):
        allowed = {"email", "password", "name", "phone", "role", "status", "company_id"}
        keys = [k for k in updates.keys() if k in allowed]
        if not keys:
            raise ValueError("No valid fields to update")

        values = [updates[k] for k in keys]
        set_clause = ", ".join(f"{k}=?" for k in keys)
        values.append(account_id)

        cur = self.conn.cursor()
        cur.execute(f"UPDATE accounts SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return {"updated_id": account_id}


    # Delete
    def delete_account(self, account_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.conn.commit()
        if cur.rowcount <= 0:
            raise ValueError("Account not found")
        return {"deleted_id": account_id}

    
    # Search
    def search_accounts_by_name(self, name, partial=True):
        """Return list of accounts matching the name."""
        cur = self.conn.cursor()
        if partial:
            cur.execute("SELECT * FROM accounts WHERE name LIKE ? COLLATE NOCASE", (f"%{name}%",))
        else:
            cur.execute("SELECT * FROM accounts WHERE name = ? COLLATE NOCASE", (name,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]