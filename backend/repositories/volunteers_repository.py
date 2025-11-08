# backend/repositories/volunteers_repository.py
from typing import Any, Dict, List, Optional

class VolunteersRepository:
    """SQLite repository for volunteers table"""

    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        return dict(row) if row is not None else None

    def create(self, *, company_id: int, name: str, email: str, phone: Optional[str]) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO volunteers (company_id, name, email, phone)
            VALUES (?, ?, ?, ?)
            """,
            (company_id, name, email, phone),
        )
        vid = cur.lastrowid
        self.conn.commit()
        return self.get_by_id(vid, company_id=company_id)

    def get_by_id(self, vol_id: int, *, company_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM volunteers WHERE id = ? AND company_id = ?",
            (vol_id, company_id),
        )
        row = cur.fetchone()
        return self._row_to_dict(row)

    def get_by_email(self, *, company_id: int, email: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM volunteers WHERE company_id = ? AND email = ?",
            (company_id, email),
        )
        row = cur.fetchone()
        return self._row_to_dict(row)

    def list(self, *, company_id: int, q: Optional[str]) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if q:
            qq = f"%{q.strip()}%"
            cur.execute(
                """
                SELECT * FROM volunteers
                 WHERE company_id = ?
                   AND (name LIKE ? OR email LIKE ? OR phone LIKE ?)
                 ORDER BY id ASC
                """,
                (company_id, qq, qq, qq),
            )
        else:
            cur.execute(
                "SELECT * FROM volunteers WHERE company_id = ? ORDER BY id ASC",
                (company_id,),
            )
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    def update(self, vol_id: int, *, company_id: int, name: str, email: str, phone: Optional[str]) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE volunteers
               SET name = ?, email = ?, phone = ?
             WHERE id = ? AND company_id = ?
            """,
            (name, email, phone, vol_id, company_id),
        )
        self.conn.commit()
        if cur.rowcount == 0:
            return None
        return self.get_by_id(vol_id, company_id=company_id)

    def delete(self, vol_id: int, *, company_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM volunteers WHERE id = ? AND company_id = ?",
            (vol_id, company_id),
        )
        self.conn.commit()
        return cur.rowcount > 0
