from typing import Dict, Any, List, Optional
from repository.db import get_conn

def list_requests() -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute("""
      SELECT r.*, a.email AS pin_email, c.name AS category_name
      FROM requests r
      LEFT JOIN accounts a ON a.id = r.pin_account_id
      LEFT JOIN categories c ON c.id = r.category_id
      ORDER BY r.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_request(req_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute("""
      SELECT r.*, a.email AS pin_email, c.name AS category_name
      FROM requests r
      LEFT JOIN accounts a ON a.id = r.pin_account_id
      LEFT JOIN categories c ON c.id = r.category_id
      WHERE r.id = ?
    """, (req_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_request(dto: Dict[str, Any]) -> Dict[str, Any]:
    # 필수값 검증(간단)
    if not dto.get("pin_account_id") or not dto.get("title"):
        raise ValueError("pin_account_id and title are required")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO requests (pin_account_id, title, description, category_id, status)
      VALUES (?,?,?,?,?)
    """, (
        int(dto["pin_account_id"]),
        dto["title"],
        dto.get("description"),
        dto.get("category_id"),
        dto.get("status", "OPEN"),
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return get_request(new_id)

def update_request(req_id: int, dto: Dict[str, Any]) -> Dict[str, Any]:
    fields, vals = [], []
    for k in ("pin_account_id","title","description","category_id","status"):
        if k in dto:
            fields.append(f"{k}=?")
            if k in ("pin_account_id","category_id") and dto[k] is not None:
                vals.append(int(dto[k]))
            else:
                vals.append(dto[k])
    if not fields:
        current = get_request(req_id)
        if not current: raise KeyError("request not found")
        return current

    vals.append(req_id)
    conn = get_conn()
    conn.execute(f"""
      UPDATE requests
      SET {', '.join(fields)}, updated_at = datetime('now')
      WHERE id = ?
    """, tuple(vals))
    conn.commit()
    conn.close()
    updated = get_request(req_id)
    if not updated: raise KeyError("request not found")
    return updated

def delete_request(req_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM requests WHERE id = ?", (req_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0
