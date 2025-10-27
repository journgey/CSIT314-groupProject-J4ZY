class CategoriesRepository:

    def __init__(self, conn):
        self.conn = conn
    
    # Create
    def create_category(self, name, description=None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description)
            )
        self.conn.commit()
        category_id = cur.lastrowid
        return {"id": category_id, "name": name, "description": description }


    # Retrieve all
    def list_categories(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM categories ORDER BY id ASC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    
    # Retrieve one
    def get_category_by_id(self, category_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    

    # Update
    def update_category(self, category_id, **updates):
        if not updates:
            raise ValueError("No fields to update")
        
        allowed = {"name", "description"}
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


    # Delete
    def delete_category(self, category_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.conn.commit()
        if cur.rowcount <= 0:
            raise ValueError("Category not found")
        return {"deleted_id": category_id}
