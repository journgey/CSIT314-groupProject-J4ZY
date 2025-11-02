from typing import Any, Dict, List, Optional


class NotificationsRepository:
    """
    SQLite repository for notifications.
    - Parameterized SQL only.
    - Returns dict rows.
    - Lists ordered by id ASC.
    """

    def __init__(self, conn):
        self.conn = conn

    # ----- Create -----
    def create(
        self,
        *,
        user_id: int,
        message: str,
        request_id: Optional[int] = None,
        actor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        cur = self.conn.cursor()
        # If your table doesn't have request_id/actor_id, remove those columns here.
        cur.execute(
            """
            INSERT INTO notifications
                (user_id, message, request_id, actor_id, created_at)
            VALUES
                (?, ?, ?, ?, datetime('now'))
            """,
            (user_id, message, request_id, actor_id),
        )
        self.conn.commit()
        nid = cur.lastrowid
        return self.get_by_id(nid)

    # ----- Read -----
    def get_by_id(self, notification_id: int) -> Dict[str, Any]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, message, request_id, actor_id, read_at, created_at
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
        SELECT id, user_id, message, request_id, actor_id, read_at, created_at
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

    # ----- Update -----
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

    # ----- Delete -----
    def delete(self, notification_id: int) -> Dict[str, Any]:
        item = self.get_by_id(notification_id)
        cur = self.conn.cursor()
        cur.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        self.conn.commit()
        return item
