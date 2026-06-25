from fastapi import APIRouter, HTTPException

from backend.app.database import get_main_connection
from backend.app.schemas.crawl import CrawlConfig, CrawlSessionResponse

router = APIRouter(prefix="/api/crawls", tags=["crawls"])


@router.get("")
def list_crawls():
    conn = get_main_connection()
    rows = conn.execute("SELECT * FROM crawl_sessions ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{session_id}")
def get_crawl(session_id: int):
    conn = get_main_connection()
    row = conn.execute("SELECT * FROM crawl_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Crawl session not found")
    return dict(row)


@router.post("", status_code=201)
def start_crawl(config: CrawlConfig):
    import json
    conn = get_main_connection()
    cur = conn.execute(
        "INSERT INTO crawl_sessions (domain, status, config) VALUES (?, 'running', ?)",
        (config.domain, config.model_dump_json()),
    )
    conn.commit()
    session_id = cur.lastrowid

    lake = get_main_connection()
    for url in config.start_urls:
        lake.execute(
            "INSERT INTO url_frontier (url, domain, depth, status, crawl_session_id) VALUES (?, ?, 0, 'pending', ?)",
            (url, config.domain, session_id),
        )
    lake.commit()
    lake.close()

    conn.close()
    return {"id": session_id, "status": "running"}
