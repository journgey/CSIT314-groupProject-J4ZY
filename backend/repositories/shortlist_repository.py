# backend/repository/shortlist_repository.py
from typing import Any, Dict, List, Optional
from sqlite3 import Row, IntegrityError

class ShortlistRepository:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _row_to_dict(row: Row) -> Dict[str, Any]:
        return dict(row)

    # Create
    def insert(self, *, csr_id: int, request_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO shortlist (csr_id, request_id)
                VALUES (?, ?)
                """,
                (csr_id, request_id),
            )
            self.conn.commit()
            return {
                "id": cur.lastrowid,
                "csr_id": csr_id,
                "request_id": request_id,
                "duplicate": False
            }

        except IntegrityError:
            # already exists → fetch existing record
            existing = self.get_by_pair(csr_id=csr_id, request_id=request_id)
            return {
                "id": existing["id"],
                "csr_id": csr_id,
                "request_id": request_id,
                "duplicate": True
            }

    # Read (single)
    def get_by_id(self, shortlist_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM shortlist WHERE id = ?", (shortlist_id,))
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def get_by_pair(self, *, csr_id: int, request_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM shortlist WHERE csr_id = ? AND request_id = ?",
            (csr_id, request_id),
        )
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    # Read list
    def list_by_csr(self, csr_id: int) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT 
                s.id AS shortlist_id,
                s.csr_id,
                s.request_id AS req_id,
                s.created_at,
                r.title,
                r.status,
                r.category_id,
                r.district_id
            FROM shortlist s
            JOIN requests r ON r.id = s.request_id
            WHERE s.csr_id = ?
            ORDER BY s.created_at DESC
            """,
            (csr_id,),
        )
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    # Delete by id
    def delete(self, shortlist_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM shortlist WHERE id = ?", (shortlist_id,))
        self.conn.commit()
        return cur.rowcount > 0

    # Delete by pair
    def delete_by_pair(self, *, csr_id: int, request_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM shortlist WHERE csr_id = ? AND request_id = ?",
            (csr_id, request_id),
        )
        self.conn.commit()
        return cur.rowcount > 0
