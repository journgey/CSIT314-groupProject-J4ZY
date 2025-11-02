from typing import Any, Dict, List
from datetime import datetime

class FeedbackService:
    def __init__(self, repo):
        self.repo = repo

    # ---------- Create ----------
    def create_feedback(self, *, request_id: int, pin_id: int, rating: int, comment: str) -> Dict[str, Any]:
        """
        Create feedback (comment + rating) for a completed request by its owning PIN.
        """
        # Validate text comment
        comment = (comment or "").strip()
        if not comment:
            raise ValueError("Comment cannot be blank")

        # Validate rating (1..5)
        if not isinstance(rating, int):
            raise ValueError("Rating must be an integer")
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        # Fetch request
        req = self.repo.get_request_min(request_id)
        if not req:
            raise ValueError("Request not found")

        # Ownership
        if req["pin_id"] != pin_id:
            raise PermissionError("Forbidden: not the owner of this request")

        # Completion check: assigned + now >= start_at
        if req["csr_id"] is None:
            raise ValueError("Feedback not allowed: request has no assigned CSR")
        start_at = req.get("start_at")
        if not start_at:
            raise ValueError("Feedback not allowed: request start time not set")
        if datetime.fromisoformat(start_at) > datetime.now():
            raise ValueError("Feedback not allowed: request is not completed yet")

        # One-time submission (no edits)
        if req.get("feedback_comment") is not None or req.get("feedback_rating") is not None:
            raise ValueError("Feedback already submitted and cannot be edited")

        # Persist
        return self.repo.set_feedback(request_id=request_id, rating=rating, comment=comment)

    # ---------- Read ----------
    def get_feedback_for_request_authorized(self, *, request_id: int, user_id: int, role: str) -> Dict[str, Any]:
        """
        Fetch feedback for a specific request if the caller is authorized:
        - PIN owner of the request or
        - CSR assigned to the request
        """
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
        """
        List all feedback entries visible to a CSR (their assignment history).
        """
        return self.repo.list_feedback_for_csr(csr_id)