import hashlib

from backend.app.database import get_main_connection


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def is_duplicate(url: str, html: str) -> bool:
    url_hash = _hash(url)
    content_hash = _hash(html)
    conn = get_main_connection()
    row = conn.execute(
        "SELECT 1 FROM records WHERE url_hash = ? OR content_hash = ? LIMIT 1",
        (url_hash, content_hash),
    ).fetchone()
    conn.close()
    return row is not None
