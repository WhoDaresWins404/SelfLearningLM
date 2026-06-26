from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from backend.app.database import get_main_connection

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("")
def list_records(container_id: int = 0, domain: str = "", status: str = "", limit: int = 50, offset: int = 0):
    conn = get_main_connection()
    params = []
    query = "SELECT r.*, c.name as container_name FROM records r LEFT JOIN containers c ON c.id = r.container_id"
    conditions = []
    if container_id:
        conditions.append("r.container_id = ?")
        params.append(container_id)
    if domain:
        conditions.append("r.domain = ?")
        params.append(domain)
    if status:
        conditions.append("r.status = ?")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
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


@router.get("/{record_id}/content", response_class=HTMLResponse)
def get_record_content(record_id: int):
    conn = get_main_connection()
    row = conn.execute(
        "SELECT source_url, raw_blob_path FROM records WHERE id = ?", (record_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Record not found")
    if not row["raw_blob_path"]:
        raise HTTPException(404, "No raw content stored for this record")
    file_path = Path(row["raw_blob_path"])
    if not file_path.exists():
        raise HTTPException(404, "Raw content file not found on disk")
    return file_path.read_text(encoding="utf-8", errors="replace")
