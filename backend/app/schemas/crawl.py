from typing import Any, Optional

from pydantic import BaseModel


class CrawlConfig(BaseModel):
    domain: str
    start_urls: list[str]
    use_proxies: bool = False
    max_pages: int = 100
    download_delay: float = 2.0
    respect_robots: bool = True


class CrawlSessionResponse(BaseModel):
    id: int
    domain: str
    status: str
    stats: dict[str, Any]
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str
