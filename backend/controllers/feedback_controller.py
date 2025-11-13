from typing import Any, Dict, List
from datetime import datetime, timezone

class FeedbackController:
    def __init__(self, repo):
        self.repo = repo

    @staticmethod
    def _to_utc_naive(s: str | None) -> datetime | None:
        if not s:
            return None
        iso = s.replace("T", " ").replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is not None:  
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt    

    def create_feedback(self, *, request_id: int, pin_id: int, rating: int, comment: str) -> Dict[str, Any]:
        comment = (comment or "").strip()
        if not comment:
            raise ValueError("Comment cannot be blank")

        if not isinstance(rating, int):
            raise ValueError("Rating must be an integer")
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        req = self.repo.get_request_min(request_id)
        if not req:
            raise ValueError("Request not found")
        if req["pin_id"] != pin_id:
            raise PermissionError("Forbidden: not the owner of this request")
        if req["csr_id"] is None:
            raise ValueError("Feedback not allowed: request has no assigned CSR")
        
        start = self._to_utc_naive(req.get("start_at"))
        end   = self._to_utc_naive(req.get("end_at"))
        now   = datetime.utcnow()  # UTC naive

        if not start:
            raise ValueError("Feedback not allowed: request start time not set")

        if end is not None:
            if end > now:
                raise ValueError("Feedback not allowed: request has not ended yet")
        else:
            if start > now:
                raise ValueError("Feedback not allowed: request is not started yet")

        if req.get("feedback_comment") is not None or req.get("feedback_rating") is not None:
            raise ValueError("Feedback already submitted and cannot be edited")

        return self.repo.set_feedback(request_id=request_id, rating=rating, comment=comment)

    def get_feedback_for_request_authorized(self, *, request_id: int, user_id: int, role: str) -> Dict[str, Any]:
        req = self.repo.get_request_min(request_id)
        if not req:
            raise ValueError("Request not found")

        if role == "PIN":
            if req["pin_id"] != user_id:
                raise PermissionError("Forbidden")
        elif role == "CSR":
            if req["csr_id"] != user_id:
                raise PermissionError("Forbidden")
        else:
            raise PermissionError("Forbidden")

        fb = self.repo.get_feedback_for_request(request_id)
        if not fb:
            raise LookupError("No feedback for this request")
        return fb

    def list_feedback_for_csr(self, *, csr_id: int) -> List[Dict[str, Any]]:
        return self.repo.list_feedback_for_csr(csr_id)