from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class FieldDefinition(BaseModel):
    name: str
    type: str = Field(description="string, number, boolean, array, object")
    description: str = ""
    selector: str = ""
    selector_type: str = "css"
    required: bool = False


class ContainerSchema(BaseModel):
    name: str
    description: str = ""
    fields: list[FieldDefinition] = []


class ContainerCreate(BaseModel):
    name: str
    description: str = ""
    schema_def: ContainerSchema


class ContainerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schema_def: Optional[ContainerSchema] = None


class ContainerResponse(BaseModel):
    id: int
    name: str
    description: str
    schema_def: dict[str, Any]
    created_at: str
    updated_at: str
