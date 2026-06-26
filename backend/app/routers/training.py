import json

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from backend.app.database import get_main_connection

router = APIRouter(prefix="/api/training", tags=["training"])


@router.get("/export")
def export_training(format: str = "", container_id: int = 0):
    conn = get_main_connection()
    params = []
    query = "SELECT td.format, td.content, r.source_url, r.domain FROM training_data td JOIN records r ON r.id = td.record_id"
    conditions = []
    if format:
        conditions.append("td.format = ?")
        params.append(format)
    if container_id:
        conditions.append("r.container_id = ?")
        params.append(container_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY td.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    lines = [json.dumps(dict(r), ensure_ascii=False) for r in rows]
    return PlainTextResponse("\n".join(lines), media_type="application/jsonl")


@router.get("/stats")
def training_stats():
    conn = get_main_connection()
    rows = conn.execute(
        "SELECT format, COUNT(*) as count FROM training_data GROUP BY format ORDER BY count DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
