from fastapi import APIRouter

from backend.app.database import get_main_connection

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("")
def list_records(container_id: int = 0, domain: str = "", limit: int = 50, offset: int = 0):
    conn = get_main_connection()
    params = []
    query = "SELECT * FROM records"
    conditions = []
    if container_id:
        conditions.append("container_id = ?")
        params.append(container_id)
    if domain:
        conditions.append("domain = ?")
        params.append(domain)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/search")
def search_records(q: str = "", limit: int = 50):
    conn = get_main_connection()
    rows = conn.execute(
        "SELECT * FROM records WHERE extracted_data LIKE ? ORDER BY quality_score DESC LIMIT ?",
        (f"%{q}%", limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
