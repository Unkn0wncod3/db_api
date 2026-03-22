from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query

from ..core.enums import EntryPermission
from ..core.errors import ForbiddenError
from ..roles import ENTRY_WRITE_ROLES, READ_ROLES
from ..schemas import (
    AccessCheckResponse,
    AttachmentLinkCreate,
    AttachmentLinkUpdate,
    AttachmentResponse,
    EntryCreate,
    EntryBundleResponse,
    EntryHistoryRecord,
    EntryLookupResponse,
    EntryPermissionCreate,
    EntryPermissionResponse,
    EntryPermissionUpdate,
    EntryRelationCreate,
    EntryRelationResponse,
    EntryRelationUpdate,
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


@router.get("/lookup", response_model=list[EntryLookupResponse])
def list_entry_lookup(
    q: Optional[str] = Query(default=None, max_length=255),
    schema_id: Optional[int] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: Optional[Dict] = Depends(get_optional_current_user),
):
    return entry_service.list_entry_lookup(current_user=current_user, search=q, schema_id=schema_id, limit=limit)


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


@router.get("/{entry_id}/relations", response_model=list[EntryRelationResponse])
def list_relations(entry_id: int, current_user: Optional[Dict] = Depends(get_optional_current_user)):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.READ)
    return relation_service.list_relations(entry_id)


@router.post("/{entry_id}/relations", response_model=EntryRelationResponse, status_code=201)
def create_relation(entry_id: int, payload: EntryRelationCreate, current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES))):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_RELATIONS)
    relation_payload = payload.model_dump()
    relation_payload["from_entry_id"] = entry_id
    return relation_service.create_relation(relation_payload)


@router.patch("/{entry_id}/relations/{relation_id}", response_model=EntryRelationResponse)
def update_relation(
    entry_id: int,
    relation_id: int,
    payload: EntryRelationUpdate,
    current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES)),
):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_RELATIONS)
    return relation_service.update_relation(entry_id, relation_id, payload.model_dump(exclude_unset=True))


@router.delete("/{entry_id}/relations/{relation_id}", response_model=EntryRelationResponse)
def delete_relation(
    entry_id: int,
    relation_id: int,
    current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES)),
):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_RELATIONS)
    return relation_service.delete_relation(entry_id, relation_id)


@router.get("/{entry_id}/permissions", response_model=list[EntryPermissionResponse])
def list_permissions(entry_id: int, current_user: Dict = Depends(require_role(*READ_ROLES))):
    entry = entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_PERMISSIONS)
    permission_service.require_access(entry, current_user, EntryPermission.MANAGE_PERMISSIONS)
    return permission_service.list_permissions(entry_id)


@router.post("/{entry_id}/permissions", response_model=EntryPermissionResponse, status_code=201)
def create_permission(entry_id: int, payload: EntryPermissionCreate, current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES))):
    entry = entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_PERMISSIONS)
    permission_service.require_access(entry, current_user, EntryPermission.MANAGE_PERMISSIONS)
    data = payload.model_dump()
    data["entry_id"] = entry_id
    data["created_by"] = current_user["id"]
    return permission_service.create_permission(data)


@router.patch("/{entry_id}/permissions/{permission_id}", response_model=EntryPermissionResponse)
def update_permission(
    entry_id: int,
    permission_id: int,
    payload: EntryPermissionUpdate,
    current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES)),
):
    entry = entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_PERMISSIONS)
    permission_service.require_access(entry, current_user, EntryPermission.MANAGE_PERMISSIONS)
    return permission_service.update_permission(entry_id, permission_id, payload.model_dump(exclude_unset=True))


@router.delete("/{entry_id}/permissions/{permission_id}", response_model=EntryPermissionResponse)
def delete_permission(
    entry_id: int,
    permission_id: int,
    current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES)),
):
    entry = entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_PERMISSIONS)
    permission_service.require_access(entry, current_user, EntryPermission.MANAGE_PERMISSIONS)
    return permission_service.delete_permission(entry_id, permission_id)


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


@router.patch("/{entry_id}/attachments/{attachment_id}", response_model=AttachmentResponse)
def update_attachment_link(
    entry_id: int,
    attachment_id: int,
    payload: AttachmentLinkUpdate,
    current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES)),
):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_ATTACHMENTS)
    return attachment_service.update_attachment_link(entry_id, attachment_id, payload.model_dump(exclude_unset=True))


@router.delete("/{entry_id}/attachments/{attachment_id}", response_model=AttachmentResponse)
def delete_attachment(
    entry_id: int,
    attachment_id: int,
    current_user: Dict = Depends(require_role(*ENTRY_WRITE_ROLES)),
):
    entry_service.get_entry(entry_id, current_user=current_user, permission=EntryPermission.MANAGE_ATTACHMENTS)
    return attachment_service.delete_attachment(entry_id, attachment_id)


@router.get("/{entry_id}/access/{permission}", response_model=AccessCheckResponse)
def check_access(entry_id: int, permission: EntryPermission, current_user: Dict = Depends(get_current_user)):
    entry = entry_service.entries.get_entry(entry_id)
    access = permission_service.get_access_map(entry, current_user)
    if not access[EntryPermission.READ.value]:
        raise ForbiddenError("Access denied for requested entry")
    return AccessCheckResponse(
        entry_id=entry_id,
        permission=permission,
        allowed=access[permission.value],
    )
