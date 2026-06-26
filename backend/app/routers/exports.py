import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.database import get_main_connection
from backend.exporter import export_training, _parse_config

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.get("/targets")
def list_targets():
    conn = get_main_connection()
    rows = conn.execute("SELECT * FROM export_targets ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/targets", status_code=201)
def create_target(name: str, type: str = "jsonl", config: str = "{}", format: str = "plain_text", auto_export: bool = False):
    conn = get_main_connection()
    cur = conn.execute(
        "INSERT INTO export_targets (name, type, config, format, auto_export) VALUES (?, ?, ?, ?, ?)",
        (name, type, config, format, int(auto_export)),
    )
    conn.commit()
    target_id = cur.lastrowid
    row = conn.execute("SELECT * FROM export_targets WHERE id = ?", (target_id,)).fetchone()
    conn.close()
    return dict(row)


@router.put("/targets/{target_id}")
def update_target(target_id: int, name: str = "", type: str = "", config: str = "", format: str = "", auto_export: bool | None = None):
    conn = get_main_connection()
    existing = conn.execute("SELECT * FROM export_targets WHERE id = ?", (target_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Export target not found")
    new_name = name or existing["name"]
    new_type = type or existing["type"]
    new_config = config if config else existing["config"]
    new_format = format if format else existing["format"]
    new_auto = int(auto_export) if auto_export is not None else existing["auto_export"]
    conn.execute(
        "UPDATE export_targets SET name=?, type=?, config=?, format=?, auto_export=? WHERE id=?",
        (new_name, new_type, new_config, new_format, new_auto, target_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM export_targets WHERE id = ?", (target_id,)).fetchone()
    conn.close()
    return dict(row)


@router.delete("/targets/{target_id}")
def delete_target(target_id: int):
    conn = get_main_connection()
    cur = conn.execute("DELETE FROM export_targets WHERE id = ?", (target_id,))
    conn.commit()
    conn.close()
    if not cur.rowcount:
        raise HTTPException(404, "Export target not found")
    return {"ok": True}


@router.post("/targets/{target_id}/trigger")
def trigger_export(target_id: int):
    conn = get_main_connection()
    target = conn.execute("SELECT * FROM export_targets WHERE id = ?", (target_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(404, "Export target not found")
    fmt = target["format"]
    # fetch training_data not yet exported to this target, with matching format
    rows = conn.execute(
        """SELECT td.id, td.format, td.content, r.source_url, r.domain, td.record_id
           FROM training_data td
           JOIN records r ON r.id = td.record_id
           WHERE (td.format = ? OR ? = 'all')
             AND NOT EXISTS (SELECT 1 FROM export_log WHERE target_id = ? AND record_id = td.record_id)
           ORDER BY td.id""",
        (fmt, fmt, target_id),
    ).fetchall()
    if not rows:
        conn.close()
        return {"exported": 0, "reason": "no new records"}

    records = [dict(r) for r in rows]
    exported = export_training(records, dict(target))
    for r in rows:
        conn.execute(
            "INSERT OR IGNORE INTO export_log (target_id, record_id) VALUES (?, ?)",
            (target_id, r["record_id"]),
        )
    conn.commit()
    conn.close()
    return {"exported": exported}


@router.get("/targets/{target_id}/stats")
def target_stats(target_id: int):
    conn = get_main_connection()
    total = conn.execute("SELECT COUNT(*) FROM export_log WHERE target_id = ?", (target_id,)).fetchone()[0]
    row = conn.execute("SELECT * FROM export_targets WHERE id = ?", (target_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Export target not found")
    return {"target_id": target_id, "total_exported": total}


@router.get("/targets/{target_id}/download")
def download_export(target_id: int):
    conn = get_main_connection()
    row = conn.execute("SELECT * FROM export_targets WHERE id = ?", (target_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Export target not found")
    config = _parse_config(row["config"])
    path_str = config.get("path", "")
    if not path_str:
        raise HTTPException(400, "No file path configured for this target")
    file_path = Path(path_str)
    if not file_path.exists():
        raise HTTPException(404, "Export file not found on disk")
    return FileResponse(str(file_path), filename=file_path.name, media_type="application/octet-stream")
