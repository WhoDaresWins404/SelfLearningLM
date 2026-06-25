from typing import Any, Optional

from pydantic import BaseModel


class RecordResponse(BaseModel):
    id: int
    content_hash: str
    url_hash: str
    source_url: str
    domain: str
    container_id: Optional[int]
    extracted_data: dict[str, Any]
    quality_score: float
    created_at: str


class RecordSearchParams(BaseModel):
    domain: Optional[str] = None
    container_id: Optional[int] = None
    q: Optional[str] = None
    limit: int = 50
    offset: int = 0
