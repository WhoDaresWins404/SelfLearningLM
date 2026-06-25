from dataclasses import dataclass
from typing import Optional


@dataclass
class Record:
    id: Optional[int]
    content_hash: str
    url_hash: str
    source_url: str
    domain: str
    container_id: Optional[int]
    extracted_data: str
    raw_blob_path: Optional[str]
    quality_score: float = 0.0
    created_at: Optional[str] = None
