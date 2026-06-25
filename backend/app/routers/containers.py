import json

from fastapi import APIRouter, HTTPException

from backend.app.schemas.container import ContainerCreate, ContainerResponse, ContainerSchema, ContainerUpdate, FieldDefinition
from backend.app.services import container_service

router = APIRouter(prefix="/api/containers", tags=["containers"])


@router.get("")
def list_containers():
    containers = container_service.list_containers()
    return [
        ContainerResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            schema_def=json.loads(c.schema_def),
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in containers
    ]


@router.get("/{container_id}")
def get_container(container_id: int):
    c = container_service.get_container(container_id)
    if not c:
        raise HTTPException(404, "Container not found")
    return ContainerResponse(
        id=c.id,
        name=c.name,
        description=c.description,
        schema_def=json.loads(c.schema_def),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.post("", status_code=201)
def create_container(body: ContainerCreate):
    c = container_service.create_container(
        name=body.name,
        description=body.description,
        schema_def=body.schema_def.model_dump(),
    )
    return ContainerResponse(
        id=c.id,
        name=c.name,
        description=c.description,
        schema_def=json.loads(c.schema_def),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.put("/{container_id}")
def update_container(container_id: int, body: ContainerUpdate):
    c = container_service.update_container(
        container_id,
        name=body.name,
        description=body.description,
        schema_def=body.schema_def.model_dump() if body.schema_def else None,
    )
    if not c:
        raise HTTPException(404, "Container not found")
    return ContainerResponse(
        id=c.id,
        name=c.name,
        description=c.description,
        schema_def=json.loads(c.schema_def),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.delete("/{container_id}")
def delete_container(container_id: int):
    if not container_service.delete_container(container_id):
        raise HTTPException(404, "Container not found")
    return {"ok": True}
