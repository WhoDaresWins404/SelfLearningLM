import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from backend.app.database import get_main_connection

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("")
def list_datasets():
    conn = get_main_connection()
    rows = conn.execute(
        """SELECT d.*, (SELECT COUNT(*) FROM dataset_records WHERE dataset_id = d.id) as record_count
           FROM datasets d ORDER BY d.created_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def create_dataset(name: str, description: str = ""):
    conn = get_main_connection()
    cur = conn.execute(
        "INSERT INTO datasets (name, description) VALUES (?, ?)",
        (name, description),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM datasets WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int):
    conn = get_main_connection()
    cur = conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    conn.commit()
    conn.close()
    if not cur.rowcount:
        raise HTTPException(404, "Dataset not found")
    return {"ok": True}


@router.get("/{dataset_id}/records")
def list_dataset_records(dataset_id: int):
    conn = get_main_connection()
    rows = conn.execute(
        """SELECT r.*, c.name as container_name
           FROM records r
           JOIN dataset_records dr ON dr.record_id = r.id
           LEFT JOIN containers c ON c.id = r.container_id
           WHERE dr.dataset_id = ?
           ORDER BY r.created_at DESC""",
        (dataset_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/{dataset_id}/records")
def add_records(dataset_id: int, record_ids: list[int]):
    conn = get_main_connection()
    existing = conn.execute("SELECT 1 FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Dataset not found")
    count = 0
    for rid in record_ids:
        cur = conn.execute(
            "INSERT OR IGNORE INTO dataset_records (dataset_id, record_id) VALUES (?, ?)",
            (dataset_id, rid),
        )
        if cur.rowcount:
            count += 1
    conn.commit()
    conn.close()
    return {"ok": True, "added": count}


@router.delete("/{dataset_id}/records")
def remove_records(dataset_id: int, record_ids: list[int]):
    conn = get_main_connection()
    for rid in record_ids:
        conn.execute(
            "DELETE FROM dataset_records WHERE dataset_id = ? AND record_id = ?",
            (dataset_id, rid),
        )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/{dataset_id}/export")
def export_dataset(dataset_id: int, format: str = ""):
    conn = get_main_connection()
    query = """
        SELECT td.format as training_format, td.content, r.source_url, r.domain
        FROM training_data td
        JOIN records r ON r.id = td.record_id
        JOIN dataset_records dr ON dr.record_id = r.id
        WHERE dr.dataset_id = ?
    """
    params = [dataset_id]
    if format:
        query += " AND td.format = ?"
        params.append(format)
    query += " ORDER BY td.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    lines = [json.dumps(dict(r), ensure_ascii=False) for r in rows]
    return PlainTextResponse("\n".join(lines), media_type="application/jsonl")
