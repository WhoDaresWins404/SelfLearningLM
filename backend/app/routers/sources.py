import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from backend.app.config import settings
from backend.app.database import get_main_connection, get_lake_connection
from backend.storage.lake import store_blob

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
def list_sources():
    conn = get_main_connection()
    rows = conn.execute("SELECT * FROM sources ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def create_source(name: str, type: str = "web", config: str = "{}", extractor_config: str = "{}", training_format: str = "plain_text", refiner_config: str = "{}"):
    conn = get_main_connection()
    cur = conn.execute(
        "INSERT INTO sources (name, type, config, extractor_config, training_format, refiner_config) VALUES (?, ?, ?, ?, ?, ?)",
        (name, type, config, extractor_config, training_format, refiner_config),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/{source_id}")
def get_source(source_id: int):
    conn = get_main_connection()
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Source not found")
    return dict(row)


@router.put("/{source_id}")
def update_source(source_id: int, name: str = "", config: str = "", extractor_config: str = "", training_format: str = "", enabled: bool = None):
    conn = get_main_connection()
    existing = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Source not found")
    new_name = name or existing["name"]
    new_config = config if config else existing["config"]
    new_extractor = extractor_config if extractor_config else existing["extractor_config"]
    new_fmt = training_format if training_format else existing["training_format"]
    new_enabled = int(enabled) if enabled is not None else existing["enabled"]
    conn.execute(
        "UPDATE sources SET name=?, config=?, extractor_config=?, training_format=?, enabled=? WHERE id=?",
        (new_name, new_config, new_extractor, new_fmt, new_enabled, source_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/{source_id}")
def delete_source(source_id: int):
    conn = get_main_connection()
    cur = conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
    conn.commit()
    conn.close()
    if not cur.rowcount:
        raise HTTPException(404, "Source not found")
    return {"ok": True}


@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...), source_id: int = 0):
    content = await file.read()
    html = content.decode("utf-8", errors="replace")
    domain = source_id or "upload"
    file_path = store_blob(
        original_url=file.filename or "uploaded_file",
        domain=str(domain),
        html_content=html,
    )
    if source_id:
        conn = get_main_connection()
        row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
        conn.close()
        source_name = row["name"] if row else str(source_id)
    else:
        source_name = file.filename or "uploaded_file"
    return {"file_path": file_path, "source_id": source_id, "source_name": source_name}
