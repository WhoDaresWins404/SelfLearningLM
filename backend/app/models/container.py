from dataclasses import dataclass
from typing import Optional


@dataclass
class Container:
    id: Optional[int]
    name: str
    description: str
    schema_def: str
    extractors: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
