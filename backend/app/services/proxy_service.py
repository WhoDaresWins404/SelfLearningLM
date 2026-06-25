from pathlib import Path
from typing import Optional

from backend.app.config import settings
from backend.app.database import get_main_connection
from backend.app.models.crawl_session import Proxy


def load_proxies_from_file(path: Optional[Path] = None) -> list[str]:
    path = path or settings.proxy_file
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]


def sync_proxies_from_file():
    proxies = load_proxies_from_file()
    if not proxies:
        return
    conn = get_main_connection()
    for addr in proxies:
        conn.execute(
            "INSERT OR IGNORE INTO proxies (address) VALUES (?)",
            (addr,),
        )
    conn.commit()
    conn.close()


def list_proxies(enabled_only: bool = False) -> list[Proxy]:
    conn = get_main_connection()
    query = "SELECT * FROM proxies"
    params = []
    if enabled_only:
        query += " WHERE enabled = 1"
    query += " ORDER BY failures ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [Proxy(**dict(r)) for r in rows]


def add_proxy(address: str) -> Proxy:
    conn = get_main_connection()
    cur = conn.execute(
        "INSERT OR IGNORE INTO proxies (address) VALUES (?)",
        (address,),
    )
    conn.commit()
    proxy_id = cur.lastrowid or conn.execute("SELECT id FROM proxies WHERE address = ?", (address,)).fetchone()[0]
    conn.close()
    return get_proxy(proxy_id)


def get_proxy(proxy_id: int) -> Optional[Proxy]:
    conn = get_main_connection()
    row = conn.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,)).fetchone()
    conn.close()
    return Proxy(**dict(row)) if row else None


def toggle_proxy(proxy_id: int, enabled: bool) -> Optional[Proxy]:
    conn = get_main_connection()
    conn.execute("UPDATE proxies SET enabled = ? WHERE id = ?", (int(enabled), proxy_id))
    conn.commit()
    conn.close()
    return get_proxy(proxy_id)


def delete_proxy(proxy_id: int) -> bool:
    conn = get_main_connection()
    cur = conn.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0
