import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.app.config import settings
from backend.app.database import get_lake_connection


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _decode_headers(headers: Optional[dict]) -> dict:
    if not headers:
        return {}
    result = {}
    for k, v in headers.items():
        key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
        if isinstance(v, (list, tuple)):
            result[key] = [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in v]
        elif isinstance(v, bytes):
            result[key] = v.decode("utf-8")
        else:
            result[key] = str(v)
    return result


def store_blob(
    original_url: str,
    domain: str,
    html_content: str,
    http_status: int = 200,
    headers: Optional[dict] = None,
    proxy_used: str = "",
    crawl_session_id: int = 0,
) -> str:
    now = datetime.utcnow()
    date_path = Path(now.strftime("%Y/%m/%d"))
    url_hash = _hash(original_url)
    content_hash = _hash(html_content)
    file_path = settings.unstructured_dir / domain / date_path / f"{url_hash}.html"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(html_content, encoding="utf-8")

    conn = get_lake_connection()
    conn.execute(
        """INSERT OR IGNORE INTO blobs
           (file_path, url_hash, content_hash, original_url, domain, http_status, headers, proxy_used, crawl_session_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(file_path), url_hash, content_hash, original_url, domain, http_status,
         json.dumps(_decode_headers(headers)), proxy_used, crawl_session_id),
    )
    conn.commit()
    conn.close()
    return str(file_path)


def add_to_frontier(url: str, domain: str, depth: int = 0, crawl_session_id: int = 0):
    conn = get_lake_connection()
    conn.execute(
        "INSERT OR IGNORE INTO url_frontier (url, domain, depth, status, crawl_session_id) VALUES (?, ?, ?, 'pending', ?)",
        (url, domain, depth, crawl_session_id),
    )
    conn.commit()
    conn.close()


def get_pending_urls(limit: int = 10) -> list[dict]:
    conn = get_lake_connection()
    rows = conn.execute(
        "SELECT * FROM url_frontier WHERE status = 'pending' ORDER BY depth ASC LIMIT ?", (limit,)
    ).fetchall()
    conn.commit()
    conn.execute(
        "UPDATE url_frontier SET status = 'in_progress' WHERE id IN (SELECT id FROM url_frontier WHERE status = 'pending' ORDER BY depth ASC LIMIT ?)",
        (limit,),
    )
    conn.commit()
    conn.close()
    return [dict(r) for r in rows]


def mark_frontier_done(frontier_id: int):
    conn = get_lake_connection()
    conn.execute("UPDATE url_frontier SET status = 'done' WHERE id = ?", (frontier_id,))
    conn.commit()
    conn.close()


def mark_frontier_failed(frontier_id: int):
    conn = get_lake_connection()
    conn.execute("UPDATE url_frontier SET status = 'failed', retries = retries + 1 WHERE id = ?", (frontier_id,))
    conn.commit()
    conn.close()


def blob_exists_by_url(url: str) -> bool:
    url_hash = _hash(url)
    conn = get_lake_connection()
    row = conn.execute("SELECT 1 FROM blobs WHERE url_hash = ?", (url_hash,)).fetchone()
    conn.close()
    return row is not None


def blob_exists_by_content(html: str) -> bool:
    content_hash = _hash(html)
    conn = get_lake_connection()
    row = conn.execute("SELECT 1 FROM blobs WHERE content_hash = ?", (content_hash,)).fetchone()
    conn.close()
    return row is not None
