from typing import Any, Dict, List, Optional
from sqlite3 import Row

# Canonical types
NOTIF_MATCH_ASSIGNED = "match_assigned"
NOTIF_REQUEST_CANCELED = "request_canceled"
NOTIF_GENERAL = "general"

class NotificationsRepository:
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _row_to_dict(row: Row) -> Dict[str, Any]:
        return dict(row)

    def create(
        self,
        *,
        user_id: int,
        message: str,
        request_id: Optional[int] = None,
        actor_id: Optional[int] = None,
        type: str = "request.accepted",  # <-- default to satisfy NOT NULL
    ) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO notifications
                (user_id, request_id, actor_id, type, message, created_at)
            VALUES
                (?, ?, ?, ?, ?, datetime('now'))
            """,
            (user_id, request_id, actor_id, type, message),
        )
        self.conn.commit()
        nid = cur.lastrowid
        return self.get_by_id(nid)
    
    def get_by_id(self, notification_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, request_id, actor_id, type, message, read_at, created_at
              FROM notifications
             WHERE id = ?
            """,
            (notification_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Notification not found")
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))

    def list_for_user(self, user_id: int, unread_only: bool) -> List[Dict[str, Any]]:
        sql = """
        SELECT id, user_id, message, request_id, actor_id, type, read_at, created_at
            FROM notifications
        WHERE user_id = ?
        """
        params = [user_id]
        if unread_only:
            sql += " AND read_at IS NULL"
        sql += " ORDER BY id ASC"
        cur = self.conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def mark_read(self, notification_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE notifications SET read_at = datetime('now') WHERE id = ?",
            (notification_id,),
        )
        if cur.rowcount == 0:
            raise ValueError("Notification not found")
        self.conn.commit()
        return self.get_by_id(notification_id)

    def mark_unread(self, notification_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE notifications SET read_at = NULL WHERE id = ?",
            (notification_id,),
        )
        if cur.rowcount == 0:
            raise ValueError("Notification not found")
        self.conn.commit()
        return self.get_by_id(notification_id)

    def delete(self, notification_id: int) -> Dict[str, Any]:
        item = self.get_by_id(notification_id)
        cur = self.conn.cursor()
        cur.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        self.conn.commit()
        return item
