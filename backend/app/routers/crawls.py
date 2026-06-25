import json
import threading

from fastapi import APIRouter, HTTPException

from backend.app.database import get_main_connection, get_lake_connection
from backend.app.schemas.crawl import CrawlConfig

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


def _run_crawl(session_id: int, domain: str, start_urls: list[str], max_pages: int, use_proxies: bool):
    from backend.crawler.engine import run_spider
    conn = get_main_connection()
    conn.execute(
        "UPDATE crawl_sessions SET started_at = datetime('now') WHERE id = ?",
        (session_id,),
    )
    conn.commit()
    conn.close()

    try:
        run_spider(domain=domain, start_urls=start_urls, max_pages=max_pages, use_proxies=use_proxies)
    except Exception as e:
        conn = get_main_connection()
        conn.execute(
            "UPDATE crawl_sessions SET status = 'failed', stats = ?, finished_at = datetime('now') WHERE id = ?",
            (json.dumps({"error": str(e)}), session_id),
        )
        conn.commit()
        conn.close()
        return

    conn = get_main_connection()
    conn.execute(
        "UPDATE crawl_sessions SET status = 'done', finished_at = datetime('now') WHERE id = ?",
        (session_id,),
    )
    conn.commit()
    conn.close()


@router.delete("/{session_id}")
def delete_crawl(session_id: int):
    conn = get_main_connection()
    cur = conn.execute("DELETE FROM crawl_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    if not cur.rowcount:
        raise HTTPException(404, "Crawl session not found")
    return {"ok": True}


@router.post("", status_code=201)
def start_crawl(config: CrawlConfig):
    conn = get_main_connection()
    cur = conn.execute(
        "INSERT INTO crawl_sessions (domain, status, config) VALUES (?, 'running', ?)",
        (config.domain, config.model_dump_json()),
    )
    conn.commit()
    session_id = cur.lastrowid

    lake = get_lake_connection()
    for url in config.start_urls:
        lake.execute(
            "INSERT INTO url_frontier (url, domain, depth, status, crawl_session_id) VALUES (?, ?, 0, 'pending', ?)",
            (url, config.domain, session_id),
        )
    lake.commit()
    lake.close()
    conn.close()

    thread = threading.Thread(
        target=_run_crawl,
        args=(session_id, config.domain, config.start_urls, config.max_pages, config.use_proxies),
        daemon=True,
    )
    thread.start()

    return {"id": session_id, "status": "running"}
