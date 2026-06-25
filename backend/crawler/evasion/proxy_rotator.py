import random
from typing import Optional

from backend.app.database import get_main_connection


class ProxyRotator:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.current_index = -1

    def get_proxy(self) -> Optional[str]:
        if not self.enabled:
            return None
        conn = get_main_connection()
        rows = conn.execute(
            "SELECT address FROM proxies WHERE enabled = 1 ORDER BY failures ASC"
        ).fetchall()
        conn.close()
        if not rows:
            return None
        self.current_index = (self.current_index + 1) % len(rows)
        return rows[self.current_index]["address"]

    def get_random_proxy(self) -> Optional[str]:
        if not self.enabled:
            return None
        conn = get_main_connection()
        rows = conn.execute(
            "SELECT address FROM proxies WHERE enabled = 1"
        ).fetchall()
        conn.close()
        if not rows:
            return None
        return random.choice(rows)["address"]

    def mark_failure(self, address: str):
        conn = get_main_connection()
        conn.execute(
            "UPDATE proxies SET failures = failures + 1 WHERE address = ?",
            (address,),
        )
        conn.commit()
        conn.close()
