from typing import Dict, Any, List, Tuple


class ReportsRepository:
    """
    Repository for reporting queries.
    Notes:
    - We compute status at a fixed anchor time (NOT 'now') to avoid time-drift.
    - For status calculation we inline the CASE expression with :anchor.
    - Date range is inclusive for both start and end (<= end 23:59:59).
    """

    def __init__(self, conn):
        self.conn = conn

    # ---------- helpers ----------

    @staticmethod
    def _status_case_sql(alias: str = "r", anchor_param: str = ":anchor") -> str:
        """
        Return a CASE expression that computes status at a given anchor time.
        Using inline CASE (instead of the view) so we can inject an anchor timestamp.
        """
        return f"""
        CASE
          WHEN datetime({anchor_param}) < datetime({alias}.start_at) AND {alias}.csr_id IS NULL THEN 'pending'
          WHEN datetime({anchor_param}) < datetime({alias}.start_at) AND {alias}.csr_id IS NOT NULL THEN 'accepted'
          WHEN datetime({anchor_param}) >= datetime({alias}.start_at) AND {alias}.csr_id IS NOT NULL THEN 'completed'
          WHEN datetime({anchor_param}) >= datetime({alias}.start_at) AND {alias}.csr_id IS NULL THEN 'expired'
        END
        """

    # ---------- Section 1: Created cohort (status distribution) ----------

    def created_status_distribution(
        self, start: str, end: str, anchor: str
    ) -> List[Dict[str, Any]]:
        """
        Return counts by computed status for requests created within [start, end].
        Columns: status, count
        """
        case_sql = self._status_case_sql(alias="r", anchor_param=":anchor")
        sql = f"""
        SELECT
          {case_sql} AS status,
          COUNT(*) AS count
        FROM requests r
        WHERE datetime(r.created_at) >= datetime(:start)
          AND datetime(r.created_at) <= datetime(:end)
        GROUP BY status
        ORDER BY status ASC;
        """
        cur = self.conn.cursor()
        cur.execute(sql, {"start": start, "end": end, "anchor": anchor})
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    # ---------- Section 2: Ended cohort performance ----------

    def ended_performance(
        self, start: str, end: str, anchor: str
    ) -> Dict[str, Any]:
        """
        Return aggregate metrics for requests whose end_at is within [start, end].
        Metrics:
          - ended_total
          - matched_count (csr_id IS NOT NULL)
          - completed_count (status == 'completed')
          - expired_count   (status == 'expired')
        """
        case_sql = self._status_case_sql(alias="r", anchor_param=":anchor")
        sql = f"""
        SELECT
          COUNT(*)                                                   AS ended_total,
          SUM(CASE WHEN r.csr_id IS NOT NULL THEN 1 ELSE 0 END)     AS matched_count,
          SUM(CASE WHEN {case_sql} = 'completed' THEN 1 ELSE 0 END) AS completed_count,
          SUM(CASE WHEN {case_sql} = 'expired'   THEN 1 ELSE 0 END) AS expired_count
        FROM requests r
        WHERE r.end_at IS NOT NULL
          AND datetime(r.end_at) >= datetime(:start)
          AND datetime(r.end_at) <= datetime(:end);
        """
        cur = self.conn.cursor()
        cur.execute(sql, {"start": start, "end": end, "anchor": anchor})
        row = cur.fetchone()
        if row is None:
            return {
                "ended_total": 0,
                "matched_count": 0,
                "completed_count": 0,
                "expired_count": 0,
            }
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    # ---------- Section 3: Regional (created & ended) ----------

    def region_counts_created(self, start: str, end: str) -> List[Dict[str, Any]]:
        """
        Created counts by region/district within [start, end].
        Columns: region, district, created_count
        """
        sql = """
        SELECT
          rg.name AS region,
          d.name  AS district,
          COUNT(*) AS created_count
        FROM requests r
        JOIN districts d ON r.district_id = d.id
        JOIN regions  rg ON d.region_id   = rg.id
        WHERE datetime(r.created_at) >= datetime(:start)
          AND datetime(r.created_at) <= datetime(:end)
        GROUP BY rg.name, d.name
        ORDER BY rg.name COLLATE NOCASE ASC, d.name COLLATE NOCASE ASC;
        """
        cur = self.conn.cursor()
        cur.execute(sql, {"start": start, "end": end})
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def region_counts_ended(self, start: str, end: str) -> List[Dict[str, Any]]:
        """
        Ended counts by region/district within [start, end].
        Columns: region, district, ended_count
        """
        sql = """
        SELECT
          rg.name AS region,
          d.name  AS district,
          COUNT(*) AS ended_count
        FROM requests r
        JOIN districts d ON r.district_id = d.id
        JOIN regions  rg ON d.region_id   = rg.id
        WHERE r.end_at IS NOT NULL
          AND datetime(r.end_at) >= datetime(:start)
          AND datetime(r.end_at) <= datetime(:end)
        GROUP BY rg.name, d.name
        ORDER BY rg.name COLLATE NOCASE ASC, d.name COLLATE NOCASE ASC;
        """
        cur = self.conn.cursor()
        cur.execute(sql, {"start": start, "end": end})
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    # ---------- Section 4: Category (created & ended) ----------

    def category_counts_created(self, start: str, end: str) -> List[Dict[str, Any]]:
        """
        Created counts by category within [start, end].
        Columns: category, created_count
        """
        sql = """
        SELECT
          c.name AS category,
          COUNT(*) AS created_count
        FROM requests r
        JOIN categories c ON r.category_id = c.id
        WHERE datetime(r.created_at) >= datetime(:start)
          AND datetime(r.created_at) <= datetime(:end)
        GROUP BY c.name
        ORDER BY c.name COLLATE NOCASE ASC;
        """
        cur = self.conn.cursor()
        cur.execute(sql, {"start": start, "end": end})
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def category_counts_ended(self, start: str, end: str) -> List[Dict[str, Any]]:
        """
        Ended counts by category within [start, end].
        Columns: category, ended_count
        """
        sql = """
        SELECT
          c.name AS category,
          COUNT(*) AS ended_count
        FROM requests r
        JOIN categories c ON r.category_id = c.id
        WHERE r.end_at IS NOT NULL
          AND datetime(r.end_at) >= datetime(:start)
          AND datetime(r.end_at) <= datetime(:end)
        GROUP BY c.name
        ORDER BY c.name COLLATE NOCASE ASC;
        """
        cur = self.conn.cursor()
        cur.execute(sql, {"start": start, "end": end})
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]
