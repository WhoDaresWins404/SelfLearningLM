import json
from typing import Optional

from backend.app.database import get_main_connection
from backend.app.models.container import Container


def list_containers() -> list[Container]:
    conn = get_main_connection()
    rows = conn.execute("SELECT * FROM containers ORDER BY name").fetchall()
    conn.close()
    return [Container(**dict(r)) for r in rows]


def get_container(container_id: int) -> Optional[Container]:
    conn = get_main_connection()
    row = conn.execute("SELECT * FROM containers WHERE id = ?", (container_id,)).fetchone()
    conn.close()
    return Container(**dict(row)) if row else None


def create_container(name: str, description: str, schema_def: dict) -> Container:
    conn = get_main_connection()
    cur = conn.execute(
        "INSERT INTO containers (name, description, schema_def) VALUES (?, ?, ?)",
        (name, description, json.dumps(schema_def)),
    )
    conn.commit()
    container_id = cur.lastrowid
    conn.close()
    return get_container(container_id)


def update_container(container_id: int, name: Optional[str] = None, description: Optional[str] = None, schema_def: Optional[dict] = None) -> Optional[Container]:
    conn = get_main_connection()
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if schema_def is not None:
        updates.append("schema_def = ?")
        params.append(json.dumps(schema_def))
    if not updates:
        conn.close()
        return get_container(container_id)
    updates.append("updated_at = datetime('now')")
    params.append(container_id)
    conn.execute(f"UPDATE containers SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return get_container(container_id)


def delete_container(container_id: int) -> bool:
    conn = get_main_connection()
    cur = conn.execute("DELETE FROM containers WHERE id = ?", (container_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0
