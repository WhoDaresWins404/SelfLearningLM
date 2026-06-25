from dataclasses import dataclass
from typing import Optional


@dataclass
class DeadLetterEntry:
    id: Optional[int]
    url: str
    domain: str
    reason: str
    metadata: str = "{}"
    crawl_session_id: Optional[int] = None
    created_at: Optional[str] = None
