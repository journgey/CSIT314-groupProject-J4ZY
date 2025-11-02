from typing import List, Dict, Any

class EngagementsRepository:
    """
    Read-only repository for engagement metrics (views and shortlist count)
    for a PIN's currently valid requests.
    """
    def __init__(self, conn):
        self.conn = conn

    def list_by_pin_current(self, pin_id: int) -> List[Dict[str, Any]]:
        """
        Return engagement metrics for the PIN's currently valid requests.
        - Validity rule:
          computed_status IN ('pending','accepted')
          AND (end_at is NULL OR end_at >= now)
        - Data source: v_requests_status for computed_status
        - Returns: id, title, start_at, end_at, computed_status, view_count, shortlist_count
        """
        sql = """
        SELECT
            v.id,
            v.title,
            v.start_at,
            v.end_at,
            v.computed_status AS status,
            v.view_count,
            COALESCE(sl.cnt, 0) AS shortlist_count
        FROM v_requests_status v
        LEFT JOIN (
            SELECT request_id, COUNT(*) AS cnt
            FROM shortlist
            GROUP BY request_id
        ) sl ON sl.request_id = v.id
        WHERE v.pin_id = ?
          AND v.computed_status IN ('pending','accepted')
          AND (v.end_at IS NULL OR datetime(v.end_at) >= datetime('now'))
        ORDER BY v.id ASC;
        """
        cur = self.conn.cursor()
        cur.execute(sql, (pin_id,))
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]
