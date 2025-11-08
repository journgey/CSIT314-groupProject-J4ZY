# backend/repositories/feedback_repository.py
from typing import Any, Dict, Optional, List

class FeedbackRepository:
    def __init__(self, conn):
        self.conn = conn

    def set_feedback(self, *, request_id: int, rating: int, comment: str) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE requests
               SET feedback_rating     = ?,
                   feedback_comment    = ?,
                   feedback_created_at = datetime('now')
             WHERE id = ?
            """,
            (rating, comment, request_id),
        )
        if cur.rowcount == 0:
            raise ValueError("Request not found")
        self.conn.commit()

        # 방금 저장된 값을 다시 읽어 반환 (end_at 포함)
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
    
    def list_by_pin_id(self, pin_id: int):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                r.id, r.pin_id, r.csr_id,
                r.category_id, r.district_id,  -- 필요 시 region_id도 포함
                r.title, r.description,
                r.start_at, r.end_at, r.created_at,
                r.view_count,
                -- ★ 피드백 3종 포함
                r.feedback_rating, r.feedback_comment, r.feedback_created_at
            FROM requests r
            WHERE r.pin_id = ?
            ORDER BY r.id ASC
            """,
            (pin_id,),
        )
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    # (B) 단건 조회
    def get_request_by_id(self, req_id: int):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT
                r.id, r.pin_id, r.csr_id,
                r.category_id, r.district_id,
                r.title, r.description,
                r.start_at, r.end_at, r.created_at,
                r.view_count,
                -- ★ 피드백 3종 포함
                r.feedback_rating, r.feedback_comment, r.feedback_created_at
            FROM requests r
            WHERE r.id = ?
            """,
            (req_id,),
        )
        row = cur.fetchone()
        if not row: return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def get_feedback_for_request(self, request_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        # 댓글이 비어있더라도 별점이 있으면 피드백이 존재하는 것으로 처리
        cur.execute(
            """
            SELECT id, pin_id, csr_id, title,
                   feedback_rating, feedback_comment, feedback_created_at
              FROM requests
             WHERE id = ?
               AND (feedback_comment IS NOT NULL OR feedback_rating IS NOT NULL)
            """,
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def list_feedback_for_csr(self, csr_id: int) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        # CSR 관점 목록에서도 rating/ comment 둘 중 하나만 있어도 노출
        cur.execute(
            """
            SELECT id, pin_id, csr_id, title,
                   feedback_rating, feedback_comment, feedback_created_at
              FROM requests
             WHERE csr_id = ?
               AND (feedback_comment IS NOT NULL OR feedback_rating IS NOT NULL)
             ORDER BY id ASC
            """,
            (csr_id,),
        )
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def get_request_min(self, request_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        # 컨트롤러에서 종료 여부 판단에 사용할 end_at 포함
        cur.execute(
            """
            SELECT id, pin_id, csr_id, start_at, end_at,
                   feedback_rating, feedback_comment
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
