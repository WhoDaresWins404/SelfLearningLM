from dataclasses import dataclass
from typing import Optional


@dataclass
class Proxy:
    id: Optional[int]
    address: str
    enabled: int = 1
    failures: int = 0
    created_at: Optional[str] = None


@dataclass
class CrawlSession:
    id: Optional[int]
    domain: str
    status: str = "pending"
    config: str = "{}"
    stats: str = "{}"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: Optional[str] = None
