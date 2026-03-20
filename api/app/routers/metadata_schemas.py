from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query

from ..roles import READ_ROLES, SCHEMA_WRITE_ROLES
from ..schemas import FieldDefinitionCreate, MetadataSchemaCreate, MetadataSchemaResponse, SchemaEntriesResponse
from ..security import get_optional_current_user, require_role
from ..services.metadata_schema import MetadataSchemaService

router = APIRouter(prefix="/schemas", tags=["schemas"])
service = MetadataSchemaService()


@router.get("", response_model=list[MetadataSchemaResponse])
def list_schemas(
    include_inactive: bool = Query(default=False),
    _: Dict = Depends(require_role(*READ_ROLES)),
):
    rows = service.list_schemas(include_inactive=include_inactive)
    return [service.get_schema(row["id"]) for row in rows]


@router.get("/{schema_id}", response_model=MetadataSchemaResponse)
def get_schema(schema_id: int, _: Dict = Depends(require_role(*READ_ROLES))):
    return service.get_schema(schema_id)


@router.get("/{schema_id}/entries", response_model=SchemaEntriesResponse)
def get_schema_entries(schema_id: int, current_user: Optional[Dict] = Depends(get_optional_current_user)):
    return service.get_schema_entries(schema_id, current_user=current_user)


@router.post("", response_model=MetadataSchemaResponse, status_code=201)
def create_schema(payload: MetadataSchemaCreate, _: Dict = Depends(require_role(*SCHEMA_WRITE_ROLES))):
    created = service.create_schema(payload.model_dump())
    return service.get_schema(created["id"])


@router.post("/{schema_id}/fields", status_code=201)
def add_field(
    schema_id: int,
    payload: FieldDefinitionCreate,
    _: Dict = Depends(require_role(*SCHEMA_WRITE_ROLES)),
):
    return service.add_field(schema_id, payload.model_dump())
