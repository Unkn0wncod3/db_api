from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query

from ..core.enums import EntryPermission
from ..roles import ENTRY_WRITE_ROLES, READ_ROLES
from ..schemas import (
    AccessCheckResponse,
    AttachmentLinkCreate,
    AttachmentResponse,
    EntryCreate,
    EntryBundleResponse,
    EntryHistoryRecord,
    EntryPermissionCreate,
    EntryRelationCreate,
    EntryResponse,
    EntryUpdate,
)
from ..security import get_current_user, get_optional_current_user, require_role
from ..services.attachments import AttachmentService
from ..services.entries import EntryService
from ..services.permissions import PermissionService
from ..services.relations import RelationService

router = APIRouter(prefix="/entries", tags=["entries"])
entry_service = EntryService()
relation_service = RelationService()
attachment_service = AttachmentService()
permission_service = PermissionService()


@router.get("", response_model=list[EntryResponse])
def list_entries(
    schema_id: Optional[int] = Query(default=None),
    owner_id: Optional[int] = Query(default=None),
    current_user: Optional[Dict] = Depends(get_optional_current_user),
):
    return entry_service.list_entries(current_user=current_user, schema_id=schema_id, owner_id=owner_id)


@router.get("/{entry_id}", response_model=EntryResponse)
def get_entry(entry_id: int, current_user: Optional[Dict] = Depends(get_optional_current_user)):
    return entry_service.get_entry(entry_id, current_user=current_user)


@router.get("/{entry_id}/bundle", response_model=EntryBundleResponse)
def get_entry_bundle(entry_id: int, current_user: Optional[Dict] = Depends(get_optional_current_user)):
    return entry_service.get_entry_bundle(entry_id, current_user=current_user)


@router.post("", response_model=EntryResponse, status_code=201)
def create_entry(payload: EntryCreate, current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES))):
    return entry_service.create_entry(payload.model_dump(), current_user=current_user)


@router.patch("/{entry_id}", response_model=EntryResponse)
def update_entry(entry_id: int, payload: EntryUpdate, current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES))):
    return entry_service.update_entry(entry_id, payload.model_dump(exclude_unset=True), current_user=current_user)


@router.get("/{entry_id}/history", response_model=list[EntryHistoryRecord])
def get_history(entry_id: int, current_user: Optional[Dict] = Depends(get_optional_current_user)):
    return entry_service.list_history(entry_id, current_user=current_user)


@router.get("/{entry_id}/relations")
def list_relations(entry_id: int, current_user: Optional[Dict] = Depends(get_optional_current_user)):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.READ)
    return relation_service.list_relations(entry_id)


@router.post("/{entry_id}/relations", status_code=201)
def create_relation(entry_id: int, payload: EntryRelationCreate, current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES))):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_RELATIONS)
    relation_payload = payload.model_dump()
    relation_payload["from_entry_id"] = entry_id
    return relation_service.create_relation(relation_payload)


@router.get("/{entry_id}/permissions")
def list_permissions(entry_id: int, current_user: Dict = Depends(require_role(*READ_ROLES))):
    entry = entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_PERMISSIONS)
    permission_service.require_access(entry, current_user, EntryPermission.MANAGE_PERMISSIONS)
    return permission_service.list_permissions(entry_id)


@router.post("/{entry_id}/permissions", status_code=201)
def create_permission(entry_id: int, payload: EntryPermissionCreate, current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES))):
    entry = entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_PERMISSIONS)
    permission_service.require_access(entry, current_user, EntryPermission.MANAGE_PERMISSIONS)
    data = payload.model_dump()
    data["entry_id"] = entry_id
    data["created_by"] = current_user["id"]
    return permission_service.create_permission(data)


@router.get("/{entry_id}/attachments", response_model=list[AttachmentResponse])
def list_attachments(entry_id: int, current_user: Optional[Dict] = Depends(get_optional_current_user)):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.READ)
    return attachment_service.list_attachments(entry_id)


@router.post("/{entry_id}/attachments", response_model=AttachmentResponse, status_code=201)
def create_attachment_link(
    entry_id: int,
    payload: AttachmentLinkCreate,
    current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES)),
):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_ATTACHMENTS)
    return attachment_service.create_attachment_link(
        entry_id=entry_id,
        file_name=payload.file_name,
        external_url=str(payload.external_url),
        mime_type=payload.mime_type,
        file_size=payload.file_size,
        checksum=payload.checksum,
        uploaded_by=current_user["id"],
        description=payload.description,
    )


@router.get("/{entry_id}/access/{permission}", response_model=AccessCheckResponse)
def check_access(entry_id: int, permission: EntryPermission, current_user: Dict = Depends(get_current_user)):
    entry = entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.READ)
    return AccessCheckResponse(
        entry_id=entry_id,
        permission=permission,
        allowed=permission_service.check_access(entry, current_user, permission),
    )
