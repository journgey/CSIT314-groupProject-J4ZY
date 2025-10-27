import json
from typing import Dict, Any, List, Optional
from sqlite3 import Row

class RequestsRepository:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _row_to_dict(row: Row) -> Dict[str, Any]:
        d = dict(row)
        # Convert volunteers TEXT(JSON) -> list
        if "volunteers" in d and isinstance(d["volunteers"], str):
            try:
                d["volunteers"] = json.loads(d["volunteers"]) if d["volunteers"] else []
            except Exception:
                d["volunteers"] = []
        return d


    def list_requests(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM requests WHERE 1=1"
        params: List[Any] = []

        if "status" in filters:
            sql += " AND status = ?"
            params.append(filters["status"])
        if "pin_id" in filters:
            sql += " AND pin_id = ?"
            params.append(filters["pin_id"])
        if "csr_id" in filters:
            sql += " AND csr_id = ?"
            params.append(filters["csr_id"])
        if "category_id" in filters:
            sql += " AND category_id = ?"
            params.append(filters["category_id"])
        if "district_id" in filters:
            sql += " AND district_id = ?"
            params.append(filters["district_id"])

        sql += " ORDER BY created_at DESC"

        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_request_by_id(self, req_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM requests WHERE id = ?", (req_id,))
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def create_request(
        self,
        *,
        pin_id: int,
        csr_id: Optional[int],
        category_id: int,
        district_id: int,
        title: str,
        description: Optional[str],
        status: str,
        start_at,
        end_at,
        created_at,
        volunteers: str,  # JSON text
    ) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO requests
                (pin_id, csr_id, category_id, district_id, title, description,
                 status, start_at, end_at, created_at, volunteers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pin_id,
                csr_id,
                category_id,
                district_id,
                title,
                description,
                status,
                start_at,
                end_at,
                created_at,
                volunteers,
            ),
        )
        self.conn.commit()
        return {"id": cur.lastrowid}

    def update_request(self, req_id: int, **data) -> Dict[str, Any]:
        if not data:
            return {"updated_id": req_id}

        fields = []
        params = []
        for k, v in data.items():
            fields.append(f"{k} = ?")
            params.append(v)
        params.append(req_id)

        sql = f"UPDATE requests SET {', '.join(fields)} WHERE id = ?"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        if cur.rowcount == 0:
            raise ValueError("Request not found")
        self.conn.commit()
        return {"updated_id": req_id}

    def delete_request(self, req_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM requests WHERE id = ?", (req_id,))
        if cur.rowcount == 0:
            raise ValueError("Request not found")
        self.conn.commit()
