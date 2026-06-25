from fastapi import APIRouter, HTTPException

from backend.app.database import get_main_connection

router = APIRouter(prefix="/api/dead-letter", tags=["dead-letter"])


@router.get("")
def list_dead_letter(domain: str = "", limit: int = 50, offset: int = 0):
    conn = get_main_connection()
    params = []
    query = "SELECT * FROM dead_letter"
    if domain:
        query += " WHERE domain = ?"
        params.append(domain)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/count")
def dead_letter_count(domain: str = ""):
    conn = get_main_connection()
    params = []
    query = "SELECT COUNT(*) FROM dead_letter"
    if domain:
        query += " WHERE domain = ?"
        params.append(domain)
    count = conn.execute(query, params).fetchone()[0]
    conn.close()
    return {"count": count}


@router.delete("/{entry_id}")
def delete_dead_letter(entry_id: int):
    conn = get_main_connection()
    cur = conn.execute("DELETE FROM dead_letter WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    if not cur.rowcount:
        raise HTTPException(404, "Entry not found")
    return {"ok": True}


@router.post("/{entry_id}/retry")
def retry_dead_letter(entry_id: int):
    conn = get_main_connection()
    entry = conn.execute("SELECT * FROM dead_letter WHERE id = ?", (entry_id,)).fetchone()
    if not entry:
        conn.close()
        raise HTTPException(404, "Entry not found")

    lake = get_main_connection()
    lake.execute(
        "INSERT INTO url_frontier (url, domain, status) VALUES (?, ?, 'pending')",
        (entry["url"], entry["domain"]),
    )
    lake.commit()
    lake.close()

    conn.execute("DELETE FROM dead_letter WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return {"ok": True}
