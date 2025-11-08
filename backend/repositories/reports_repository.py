from typing import Dict, Any, List

class ReportsRepository:
  
  def __init__(self, conn):
    self.conn = conn
    
  def created_status_distribution(self, start: str, end: str) -> List[Dict[str, Any]]:
    sql = """
    SELECT
      vs.computed_status AS status,
      COUNT(*)           AS count
    FROM v_requests_status vs
    WHERE datetime(vs.created_at) >= datetime(:start)
      AND datetime(vs.created_at) <= datetime(:end)
    GROUP BY vs.computed_status
    ORDER BY status ASC;
    """
    cur = self.conn.cursor()
    cur.execute(sql, {"start": start, "end": end})
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]

  def ended_performance(self, start: str, end: str) -> Dict[str, Any]:
    sql = """
    SELECT
      COUNT(*)                                                   AS ended_total,
      SUM(CASE WHEN vs.computed_status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
      SUM(CASE WHEN vs.computed_status = 'expired'   THEN 1 ELSE 0 END) AS expired_count
    FROM v_requests_status vs
    WHERE vs.end_at IS NOT NULL
      AND datetime(vs.end_at) >= datetime(:start)
      AND datetime(vs.end_at) <= datetime(:end);
    """
    cur = self.conn.cursor()
    cur.execute(sql, {"start": start, "end": end})
    row = cur.fetchone()
    if row is None:
        return {
            "ended_total": 0,
            "completed_count": 0,
            "expired_count": 0,
        }
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))

  def region_counts_created(self, start: str, end: str) -> List[Dict[str, Any]]:
      sql = """
      SELECT
        vr.region_name   AS region,
        vr.district_name AS district,
        COUNT(*)         AS created_count
      FROM v_requests vr
      WHERE datetime(vr.created_at) >= datetime(:start)
        AND datetime(vr.created_at) <= datetime(:end)
      GROUP BY vr.region_name, vr.district_name
      ORDER BY vr.region_name COLLATE NOCASE ASC,
                vr.district_name COLLATE NOCASE ASC;
      """
      cur = self.conn.cursor()
      cur.execute(sql, {"start": start, "end": end})
      rows = cur.fetchall()
      cols = [c[0] for c in cur.description]
      return [dict(zip(cols, r)) for r in rows]

  def region_counts_ended(self, start: str, end: str) -> List[Dict[str, Any]]:
      sql = """
      SELECT
        vr.region_name   AS region,
        vr.district_name AS district,
        COUNT(*)         AS ended_count
      FROM v_requests vr
      WHERE vr.end_at IS NOT NULL
        AND datetime(vr.end_at) >= datetime(:start)
        AND datetime(vr.end_at) <= datetime(:end)
      GROUP BY vr.region_name, vr.district_name
      ORDER BY vr.region_name COLLATE NOCASE ASC,
                vr.district_name COLLATE NOCASE ASC;
      """
      cur = self.conn.cursor()
      cur.execute(sql, {"start": start, "end": end})
      rows = cur.fetchall()
      cols = [c[0] for c in cur.description]
      return [dict(zip(cols, r)) for r in rows]

  def category_counts_created(self, start: str, end: str) -> List[Dict[str, Any]]:
      sql = """
      SELECT
        vr.category_name AS category,
        COUNT(*)         AS created_count
      FROM v_requests vr
      WHERE datetime(vr.created_at) >= datetime(:start)
        AND datetime(vr.created_at) <= datetime(:end)
      GROUP BY vr.category_name
      ORDER BY vr.category_name COLLATE NOCASE ASC;
      """
      cur = self.conn.cursor()
      cur.execute(sql, {"start": start, "end": end})
      rows = cur.fetchall()
      cols = [c[0] for c in cur.description]
      return [dict(zip(cols, r)) for r in rows]

  def category_counts_ended(self, start: str, end: str) -> List[Dict[str, Any]]:
      sql = """
      SELECT
        vr.category_name AS category,
        COUNT(*)         AS ended_count
      FROM v_requests vr
      WHERE vr.end_at IS NOT NULL
        AND datetime(vr.end_at) >= datetime(:start)
        AND datetime(vr.end_at) <= datetime(:end)
      GROUP BY vr.category_name
      ORDER BY vr.category_name COLLATE NOCASE ASC;
      """
      cur = self.conn.cursor()
      cur.execute(sql, {"start": start, "end": end})
      rows = cur.fetchall()
      cols = [c[0] for c in cur.description]
      return [dict(zip(cols, r)) for r in rows]