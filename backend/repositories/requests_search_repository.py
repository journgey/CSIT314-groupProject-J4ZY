import json
from typing import Dict, Any, List
from sqlite3 import Row


class RequestsSearchRepository:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _row_to_dict(row: Row) -> Dict[str, Any]:
        d = dict(row)
        if "volunteers" in d and isinstance(d["volunteers"], str):
            try:
                d["volunteers"] = json.loads(d["volunteers"]) if d["volunteers"] else []
            except Exception:
                d["volunteers"] = []
        return d
    
    def _in_clause(self, vals):
        placeholders = ",".join(["?"] * len(vals))
        return placeholders, list(vals)

    def search_requests(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            v.id, v.pin_id, v.pin_name,
            v.csr_id, v.csr_name,
            v.category_id, v.category_name,
            v.district_id, v.district_name,
            v.region_id, v.region_name,
            v.title, v.description,
            v.start_at, v.end_at, v.created_at,
            v.view_count,
            v.feedback_rating, v.feedback_comment, v.feedback_created_at,
            v.status,
            v.volunteers, v.volunteers_count, v.volunteer_names
        FROM v_requests v
        WHERE 1=1
        """
        params = []

        if filters.get("pin_id") is not None:
            sql += " AND v.pin_id = ?"
            params.append(filters["pin_id"])
        if filters.get("csr_id") is not None:
            sql += " AND v.csr_id = ?"
            params.append(filters["csr_id"])

        # --- filters ---
        if filters.get("category_id") is not None:
            sql += " AND v.category_id = ?"
            params.append(filters["category_id"])

        if filters.get("region_id") is not None:
            sql += " AND v.region_id = ?"
            params.append(filters["region_id"])

        if filters.get("district_id") is not None:
            sql += " AND v.district_id = ?"
            params.append(filters["district_id"])

        if filters.get("created_at"):
            sql += " AND DATE(v.created_at) = DATE(?)"
            params.append(filters["created_at"])

        start_at = filters.get("start_at")
        end_at = filters.get("end_at")
        if start_at and end_at:
            sql += " AND DATE(v.start_at) >= DATE(?) AND DATE(v.end_at) <= DATE(?)"
            params.extend([start_at, end_at])
        elif start_at:
            sql += " AND DATE(v.start_at) >= DATE(?)"
            params.append(start_at)
        elif end_at:
            sql += " AND DATE(v.end_at) <= DATE(?)"
            params.append(end_at)

        q = (filters.get("q") or "").strip()
        if q:
            sql += " AND LOWER(v.title) LIKE LOWER(?)"
            params.append(f"%{q}%")

        status_list = filters.get("status_list")
        if status_list:
            ph, vs = self._in_clause(status_list)
            sql += f" AND LOWER(v.status) IN ({ph})"
            params.extend(vs)

        allowed_sort = {"created_at", "start_at", "end_at", "view_count", "id", "title"}
        sort = str(filters.get("sort", "created_at"))
        if sort not in allowed_sort:
            sort = "created_at"

        order = str(filters.get("order", "DESC")).upper()
        order = "DESC" if order not in {"ASC", "DESC"} else order

        limit = int(filters.get("limit", 20))
        offset = int(filters.get("offset", 0))

        sql += f" ORDER BY v.{sort} {order}, v.id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    def search_history(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        sql = """
        SELECT
            v.id, v.pin_id, v.pin_name,
            v.csr_id, v.csr_name,
            v.category_id, v.category_name,
            v.district_id, v.district_name,
            v.region_id, v.region_name,
            v.title, v.description,
            v.start_at, v.end_at, v.created_at,
            v.view_count,
            v.feedback_rating, v.feedback_comment, v.feedback_created_at,
            v.status,
            v.volunteers, v.volunteers_count, v.volunteer_names
        FROM v_requests v
        WHERE 1=1
        """
        params: List[Any] = []

        scope = filters.get("history_scope")
        if scope == "pin":
            sql += " AND v.pin_id = ?"
            params.append(filters["pin_id"])
            sql += " AND v.status IN ('completed','expired')"
        elif scope == "csr":
            sql += " AND v.csr_id = ?"
            params.append(filters["csr_id"])
            sql += " AND v.status = 'completed'"
        else:
            raise ValueError("history_scope must be 'pin' or 'csr'")

        sql += " AND DATE(v.end_at) < DATE('now','localtime')"

        if filters.get("category_id") is not None:
            sql += " AND v.category_id = ?"
            params.append(filters["category_id"])

        if filters.get("date_from"):
            sql += " AND DATE(v.end_at) >= DATE(?)"
            params.append(filters["date_from"])
        if filters.get("date_to"):
            sql += " AND DATE(v.end_at) <= DATE(?)"
            params.append(filters["date_to"])

        if filters.get("only_with_feedback"):
            sql += " AND (v.feedback_rating IS NOT NULL OR v.feedback_comment IS NOT NULL OR v.feedback_created_at IS NOT NULL)"

        allowed_sort = {"end_at", "created_at", "start_at", "id", "title", "view_count"}
        sort = str(filters.get("sort", "end_at"))
        if sort not in allowed_sort:
            sort = "end_at"

        order = str(filters.get("order", "DESC")).upper()
        order = "DESC" if order not in {"ASC", "DESC"} else order

        limit = int(filters.get("limit", 20))
        offset = int(filters.get("offset", 0))

        sql += f" ORDER BY v.{sort} {order}, v.id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]
