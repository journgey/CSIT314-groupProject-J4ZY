from typing import Any, Dict, List, Optional


class NotificationsService:
    """
    Service for notifications.
    - Validates inputs and ownership.
    - Provides helpers to format one-line messages for common events.
    """

    def __init__(self, repo):
        self.repo = repo

    # ---------- Creation (general) ----------
    def create_notification(
        self,
        *,
        user_id: int,
        message: str,
        request_id: Optional[int] = None,
        actor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user_id")
        msg = (message or "").strip()
        if not msg:
            raise ValueError("Invalid message")
        return self.repo.create(
            user_id=user_id,
            message=msg,
            request_id=request_id,
            actor_id=actor_id,
        )

    # ---------- Creation (domain helpers) ----------
    @staticmethod
    def _fmt_pin_deleted_request(actor_name: str, request_title: str) -> str:
        # CSR에게: "**님이 (제목~~)요청을 삭제하였습니다"
        return f"{actor_name}님이 ({request_title}) 요청을 삭제하였습니다"

    @staticmethod
    def _fmt_csr_accepted_request(actor_name: str, request_title: str) -> str:
        # PIN에게: "**님이 (제목~~)요청을 수락하였습니다"
        return f"{actor_name}님이 ({request_title}) 요청을 수락하였습니다"

    def create_for_pin_deleted_request(
        self,
        *,
        csr_user_id: int,
        actor_name: str,
        request_title: str,
        request_id: Optional[int] = None,
        actor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        msg = self._fmt_pin_deleted_request(actor_name, request_title)
        return self.create_notification(
            user_id=csr_user_id,
            message=msg,
            request_id=request_id,
            actor_id=actor_id,
        )

    def create_for_csr_accepted_request(
        self,
        *,
        pin_user_id: int,
        actor_name: str,
        request_title: str,
        request_id: Optional[int] = None,
        actor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        msg = self._fmt_csr_accepted_request(actor_name, request_title)
        return self.create_notification(
            user_id=pin_user_id,
            message=msg,
            request_id=request_id,
            actor_id=actor_id,
        )

    # ---------- Read ----------
    def list_for_user(self, *, user_id: int, unread_only: bool = False) -> List[Dict[str, Any]]:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user_id")
        return self.repo.list_for_user(user_id, unread_only)

    # Ownership checks: caller must pass current_user_id from controller
    def _ensure_owner(self, notification_id: int, current_user_id: int) -> Dict[str, Any]:
        item = self.repo.get_by_id(notification_id)
        if item["user_id"] != current_user_id:
            raise PermissionError("Forbidden")
        return item

    # ---------- Update ----------
    def mark_read(self, *, notification_id: int, current_user_id: int) -> Dict[str, Any]:
        self._ensure_owner(notification_id, current_user_id)
        return self.repo.mark_read(notification_id)

    def mark_unread(self, *, notification_id: int, current_user_id: int) -> Dict[str, Any]:
        self._ensure_owner(notification_id, current_user_id)
        return self.repo.mark_unread(notification_id)

    # ---------- Delete ----------
    def delete(self, *, notification_id: int, current_user_id: int) -> Dict[str, Any]:
        self._ensure_owner(notification_id, current_user_id)
        return self.repo.delete(notification_id)
