# backend/repositories/shortlist_repository.py
from typing import Any, Dict, List, Optional
from sqlite3 import Row, IntegrityError

class ShortlistRepository:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _row_to_dict(row: Row) -> Dict[str, Any]:
        return dict(row)

    def insert(self, *, csr_id: int, request_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        try:
            # Insert shortlist pair
            cur.execute(
                """
                INSERT INTO shortlist (csr_id, request_id)
                VALUES (?, ?)
                """,
                (csr_id, request_id),
            )
            # Bump shortlist_count on the corresponding request (atomic with same connection)
            cur.execute(
                """
                UPDATE requests
                   SET shortlist_count = COALESCE(shortlist_count, 0) + 1
                 WHERE id = ?
                """,
                (request_id,),
            )

            self.conn.commit()
            return {
                "id": cur.lastrowid,
                "csr_id": csr_id,
                "request_id": request_id,
                "duplicate": False
            }

        except IntegrityError:
            # Unique pair already exists → do not change the counter
            existing = self.get_by_pair(csr_id=csr_id, request_id=request_id)
            return {
                "id": existing["id"],
                "csr_id": csr_id,
                "request_id": request_id,
                "duplicate": True
            }

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

    def list_by_csr(self, csr_id: int, only_pending: bool = False) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        base_sql = """
            SELECT
                s.id               AS shortlist_id,
                s.csr_id,
                s.request_id,
                s.created_at       AS shortlisted_at,

                v.id               AS id,
                v.pin_id,
                v.pin_name,
                v.csr_id           AS assigned_csr_id,
                v.csr_name,

                v.category_id,
                v.category_name,
                v.district_id,
                v.district_name,
                v.region_id,
                v.region_name,

                v.title,
                v.description,
                v.start_at,
                v.end_at,
                v.created_at       AS request_created_at,
                v.view_count,

                v.feedback_rating,
                v.feedback_comment,
                v.feedback_created_at,

                v.status,

                v.volunteers,
                v.volunteers_count,
                v.volunteer_names
            FROM shortlist s
            JOIN v_requests v
              ON v.id = s.request_id
            WHERE s.csr_id = ?
        """
        params = [csr_id]
        if only_pending:
            base_sql += " AND (v.status IS NULL OR LOWER(v.status) IN ('requested','pending'))"
        base_sql += " ORDER BY s.created_at DESC"
        cur.execute(base_sql, params)
        rows = cur.fetchall()
        return [self._row_to_dict(r) for r in rows]

    def delete(self, shortlist_id: int) -> bool:
        """Delete by shortlist row id and decrement the parent request counter if a row was deleted."""
        cur = self.conn.cursor()

        # Get the request_id before deletion to update the counter correctly
        cur.execute("SELECT request_id FROM shortlist WHERE id = ?", (shortlist_id,))
        row = cur.fetchone()
        if not row:
            return False
        request_id = row["request_id"] if isinstance(row, Row) else row[0]

        # Delete the shortlist row
        cur.execute("DELETE FROM shortlist WHERE id = ?", (shortlist_id,))
        deleted = cur.rowcount > 0

        # Decrement counter (floor at 0) only if a row was actually deleted
        if deleted:
            cur.execute(
                """
                UPDATE requests
                   SET shortlist_count = CASE
                        WHEN shortlist_count IS NULL THEN 0
                        WHEN shortlist_count > 0 THEN shortlist_count - 1
                        ELSE 0
                       END
                 WHERE id = ?
                """,
                (request_id,),
            )

        self.conn.commit()
        return deleted

    def delete_by_pair(self, *, csr_id: int, request_id: int) -> bool:
        """Delete by (csr_id, request_id) and decrement the counter if a row was deleted."""
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM shortlist WHERE csr_id = ? AND request_id = ?",
            (csr_id, request_id),
        )
        deleted = cur.rowcount > 0

        if deleted:
            cur.execute(
                """
                UPDATE requests
                   SET shortlist_count = CASE
                        WHEN shortlist_count IS NULL THEN 0
                        WHEN shortlist_count > 0 THEN shortlist_count - 1
                        ELSE 0
                       END
                 WHERE id = ?
                """,
                (request_id,),
            )

        self.conn.commit()
        return deleted
    
    def get_pin_shortlist_count(self, pin_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COUNT(*) 
            FROM shortlist s
            JOIN requests r ON r.id = s.request_id
            WHERE r.pin_id = ?
        """, (pin_id,))
        (count,) = cur.fetchone()
        return count

    def clear_for_request(self, request_id: int) -> int:
        """Remove all shortlist rows for a request and reset its counter to 0."""
        cur = self.conn.cursor()

        # Delete all shortlist rows for this request
        cur.execute("DELETE FROM shortlist WHERE request_id = ?", (request_id,))
        deleted = cur.rowcount

        # Reset denormalised counter on the parent request
        cur.execute(
            "UPDATE requests SET shortlist_count = 0 WHERE id = ?",
            (request_id,),
        )

        self.conn.commit()
        return deleted
