from typing import Optional, Dict, Any

class AuthRepository:
    def __init__(self, conn):
        self.conn = conn

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM accounts WHERE email=? COLLATE NOCASE LIMIT 1", (email.strip(),))
        row = cur.fetchone()
        return dict(row) if row else None