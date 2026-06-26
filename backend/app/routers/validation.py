from fastapi import APIRouter, HTTPException

from backend.app.database import get_main_connection

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.get("/pending")
def list_pending(limit: int = 50, offset: int = 0, status: str = "pending"):
    conn = get_main_connection()
    rows = conn.execute(
        """SELECT r.*, c.name as container_name
           FROM records r LEFT JOIN containers c ON c.id = r.container_id
           WHERE r.status = ?
           ORDER BY r.quality_score DESC, r.created_at ASC
           LIMIT ? OFFSET ?""",
        (status, limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/stats")
def validation_stats():
    conn = get_main_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM records GROUP BY status"
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    conn.close()
    stats = {r["status"]: r["count"] for r in rows}
    return {
        "total": total,
        "pending": stats.get("pending", 0),
        "approved": stats.get("approved", 0),
        "rejected": stats.get("rejected", 0),
    }


@router.get("/{record_id}")
def get_record(record_id: int):
    conn = get_main_connection()
    row = conn.execute(
        "SELECT r.*, c.name as container_name FROM records r LEFT JOIN containers c ON c.id = r.container_id WHERE r.id = ?",
        (record_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Record not found")
    return dict(row)


@router.post("/{record_id}/approve")
def approve_record(record_id: int):
    conn = get_main_connection()
    row = conn.execute("SELECT status FROM records WHERE id = ?", (record_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Record not found")
    conn.execute(
        "UPDATE records SET status = 'approved', validated_at = datetime('now') WHERE id = ?",
        (record_id,),
    )
    conn.execute(
        "INSERT INTO validation_log (record_id, action) VALUES (?, 'approved')",
        (record_id,),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/{record_id}/reject")
def reject_record(record_id: int, notes: str = ""):
    conn = get_main_connection()
    row = conn.execute("SELECT status FROM records WHERE id = ?", (record_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Record not found")
    conn.execute(
        "UPDATE records SET status = 'rejected', validated_at = datetime('now'), reviewer_notes = ? WHERE id = ?",
        (notes, record_id),
    )
    conn.execute(
        "INSERT INTO validation_log (record_id, action, notes) VALUES (?, 'rejected', ?)",
        (record_id, notes),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/{record_id}/edit")
def edit_record(record_id: int, extracted_data: str, notes: str = ""):
    conn = get_main_connection()
    row = conn.execute("SELECT status FROM records WHERE id = ?", (record_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Record not found")
    conn.execute(
        "UPDATE records SET status = 'approved', extracted_data = ?, validated_at = datetime('now'), reviewer_notes = ? WHERE id = ?",
        (extracted_data, notes, record_id),
    )
    conn.execute(
        "INSERT INTO validation_log (record_id, action, notes) VALUES (?, 'edited', ?)",
        (record_id, notes),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/batch")
def batch_action(record_ids: list[int], action: str, notes: str = ""):
    if action not in ("approve", "reject"):
        raise HTTPException(400, "Invalid action. Use 'approve' or 'reject'.")
    conn = get_main_connection()
    status = "approved" if action == "approve" else "rejected"
    for rid in record_ids:
        conn.execute(
            "UPDATE records SET status = ?, validated_at = datetime('now'), reviewer_notes = ? WHERE id = ?",
            (status, notes, rid),
        )
        conn.execute(
            "INSERT INTO validation_log (record_id, action, notes) VALUES (?, ?, ?)",
            (rid, action, notes),
        )
    conn.commit()
    conn.close()
    return {"ok": True, "count": len(record_ids)}
