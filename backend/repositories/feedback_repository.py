# backend/repositories/feedback_repository.py
from typing import Any, Dict, Optional, List

class FeedbackRepository:
    def __init__(self, conn):
        self.conn = conn

    def set_feedback(self, *, request_id: int, rating: int, comment: str) -> Dict[str, Any]:
        """
        Persist feedback_comment, feedback_rating and feedback_created_at for a request.
        Returns a compact projection of the updated row.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE requests
               SET feedback_rating  = ?, 
                   feedback_comment = ?, 
                   feedback_created_at = datetime('now')
             WHERE id = ?
            """,
            (rating, comment, request_id),
        )
        if cur.rowcount == 0:
            raise ValueError("Request not found")
        self.conn.commit()

        cur.execute(
            """
            SELECT id, pin_id, csr_id, title, start_at, end_at,
                   feedback_rating, feedback_comment, feedback_created_at
              FROM requests
             WHERE id = ?
            """,
            (request_id,),
        )
        row = cur.fetchone()
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def get_feedback_for_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Return feedback fields for a request if present; otherwise None.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, pin_id, csr_id, title,
                   feedback_rating, feedback_comment, feedback_created_at
              FROM requests
             WHERE id = ? AND feedback_comment IS NOT NULL
            """,
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def list_feedback_for_csr(self, csr_id: int) -> List[Dict[str, Any]]:
        """
        List all requests in CSR's history that have feedback.
        Ordered by id ASC.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, pin_id, csr_id, title,
                   feedback_rating, feedback_comment, feedback_created_at
              FROM requests
             WHERE csr_id = ?
               AND feedback_comment IS NOT NULL
             ORDER BY id ASC
            """,
            (csr_id,),
        )
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def get_request_min(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Minimal request fetch for ownership/assignment checks.
        """
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, pin_id, csr_id, start_at, feedback_rating, 
                   feedback_comment
              FROM requests
             WHERE id = ?
            """,
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))