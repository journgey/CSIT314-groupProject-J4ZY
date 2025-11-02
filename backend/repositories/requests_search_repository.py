import json
from typing import Dict, Any, List
from sqlite3 import Row


class RequestsSearchRepository:
    """Repository layer for searching and filtering requests with related tables."""

    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _row_to_dict(row: Row) -> Dict[str, Any]:
        """Convert SQLite Row to a dictionary and parse volunteers JSON."""
        d = dict(row)
        if "volunteers" in d and isinstance(d["volunteers"], str):
            try:
                d["volunteers"] = json.loads(d["volunteers"]) if d["volunteers"] else []
            except Exception:
                d["volunteers"] = []
        return d

    def search_requests(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run a search query for requests with optional filters.

        Filters:
            - category_id: int
            - region_id: int
            - district_id: int
            - created_at: str (ISO 8601 format: 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ')
            - start_at, end_at: str (ISO 8601 format: 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ')
            - sort: str (allowed: id, created_at, start_at, end_at)
            - order: str (asc / desc)
            - limit: int
            - offset: int
        """
        sql = """
        SELECT
            r.id,
            r.pin_id,
            r.csr_id,
            r.category_id,
            c.name AS category_name,
            r.district_id,
            d.name AS district_name,
            rg.name AS region_name,
            r.title,
            r.description,
            r.status,
            r.start_at,
            r.end_at,
            r.created_at,
            r.volunteers
        FROM requests r
        JOIN categories c ON r.category_id = c.id
        JOIN districts d ON r.district_id = d.id
        JOIN regions rg ON d.region_id = rg.id
        WHERE 1=1
        """

        params: List[Any] = []

        if "category_id" in filters:
            sql += " AND r.category_id = ?"
            params.append(filters["category_id"])

        if "region_id" in filters:
            sql += " AND d.region_id = ?"
            params.append(filters["region_id"])

        if "district_id" in filters:
            sql += " AND r.district_id = ?"
            params.append(filters["district_id"])

        if "created_at" in filters:
            sql += " AND DATE(r.created_at) = DATE(?)"
            params.append(filters["created_at"])

        if "start_at" in filters and "end_at" in filters:
            sql += " AND DATE(r.start_at) >= DATE(?) AND DATE(r.end_at) <= DATE(?)"
            params.extend([filters["start_at"], filters["end_at"]])
        elif "start_at" in filters:
            sql += " AND DATE(r.start_at) >= DATE(?)"
            params.append(filters["start_at"])
        elif "end_at" in filters:
            sql += " AND DATE(r.end_at) <= DATE(?)"
            params.append(filters["end_at"])

        sort = filters.get("sort", "created_at")
        order = filters.get("order", "desc").upper()
        limit = filters.get("limit", 20)
        offset = filters.get("offset", 0)

        sql += f" ORDER BY r.{sort} {order}, r.id ASC"
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]
