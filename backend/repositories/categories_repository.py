class CategoriesRepository:
    def __init__(self, conn):
        self.conn = conn

    def create_category(self, name, description=None, status="active"):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO categories (name, description, status) VALUES (?, ?, ?)",
            (name, description, status),
        )
        self.conn.commit()
        category_id = cur.lastrowid
        return {
            "id": category_id,
            "name": name,
            "description": description,
            "status": status,
        }

    def list_categories(self, include_inactive=False):
        cur = self.conn.cursor()
        if include_inactive:
            cur.execute("SELECT * FROM categories ORDER BY id ASC")
        else:
            cur.execute(
                "SELECT * FROM categories WHERE status='active' ORDER BY id ASC"
            )
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_category_by_id(self, category_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_category(self, category_id, **updates):
        if not updates:
            raise ValueError("No fields to update")

        allowed = {"name", "description", "status"}
        keys = [k for k in updates.keys() if k in allowed]
        if not keys:
            raise ValueError("No valid fields to update")

        values = [updates[k] for k in keys]
        set_clause = ", ".join(f"{k}=?" for k in keys)
        values.append(category_id)

        cur = self.conn.cursor()
        cur.execute(f"UPDATE categories SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return {"updated_id": category_id}

    def deactivate_category(self, category_id):
        """Soft delete: set status to inactive instead of removing"""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE categories SET status='inactive' WHERE id = ?", (category_id,)
        )
        self.conn.commit()
        if cur.rowcount <= 0:
            raise ValueError("Category not found")
        return {"deactivated_id": category_id}
