from datetime import time
import sqlite3
from typing import Any, Dict, List, Optional

class RequestsRepository:
    
    def __init__(self, conn):
        self.conn = conn

    def create_request(
        self, *, pin_id: int, csr_id: Optional[int], category_id: int, district_id: int,
        title: str, description: Optional[str], start_at: Optional[str], end_at: Optional[str],
        volunteers: Optional[str],
    ) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO requests
              (pin_id, csr_id, category_id, district_id, title, description,
               start_at, end_at, volunteers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pin_id, csr_id, category_id, district_id, title, description, start_at, end_at, volunteers),
        )
        self.conn.commit()
        return self.get_request_by_id(cur.lastrowid)

    def get_request_by_id(self, req_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT v.* FROM v_requests v WHERE v.id = ?", (req_id,))
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def list_requests(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = ["SELECT * FROM v_requests WHERE 1=1"]
        args = []

        if filters.get("status"):
            sql.append("AND status = ?")
            args.append(filters["status"])

        for f in ("pin_id", "csr_id", "category_id", "district_id"):
            if filters.get(f) is not None:
                sql.append(f"AND {f} = ?")
                args.append(filters[f])

        sql.append("ORDER BY id ASC")
        cur = self.conn.cursor()
        cur.execute(" ".join(sql), args)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def update_request(self, req_id: int, **fields) -> Optional[Dict[str, Any]]:
        to_set, args = [], []
        for k, v in fields.items():
            if k in {
                "title", "description", "start_at", "end_at",
                "category_id", "district_id", "volunteers", "view_count"
            }:
                to_set.append(f"{k} = ?")
                args.append(v)
        if not to_set:
            return self.get_request_by_id(req_id)
        args.append(req_id)
        cur = self.conn.cursor()
        cur.execute(f"UPDATE requests SET {', '.join(to_set)} WHERE id = ?", args)
        if cur.rowcount == 0:
            return None
        self.conn.commit()
        return self.get_request_by_id(req_id)

    def delete_request(self, req_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM requests WHERE id = ?", (req_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def try_assign_csr(self, *, request_id: int, csr_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE requests SET csr_id = ? WHERE id = ? AND csr_id IS NULL",
            (csr_id, request_id),
        )
        self.conn.commit()
        return cur.rowcount == 1
    
    def update_volunteers(self, *, request_id: int, volunteers_json: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute("UPDATE requests SET volunteers = ? WHERE id = ?", (volunteers_json, request_id))
        if cur.rowcount == 0:
            raise ValueError("Request not found")
        self.conn.commit()
        return self.get_request_by_id(request_id)

    def increment_view_count(self, req_id: int, *, retries: int = 3, delay: float = 0.05) -> bool:
        """Try to increment view_count with small retries. Returns True on success, False otherwise."""
        for i in range(retries):
            try:
                cur = self.conn.cursor()
                cur.execute("UPDATE requests SET view_count = view_count + 1 WHERE id = ?", (req_id,))
                self.conn.commit()
                return True
            except sqlite3.OperationalError as e:
                # only retry on lock
                if "locked" not in str(e).lower():
                    raise
                time.sleep(delay * (i + 1))
        return False