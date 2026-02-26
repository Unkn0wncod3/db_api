from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..roles import ADMIN_ROLES
from ..schemas import UserCreate, UserListResponse, UserResponse, UserStatusUpdate, UserUpdate
from ..security import require_role
from ..services import audit_logs, users as user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("", response_model=UserListResponse)
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: Dict = Depends(require_role(*ADMIN_ROLES)),
):
    return user_service.list_users(limit=limit, offset=offset)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, request: Request, current_user: Dict = Depends(require_role(*ADMIN_ROLES))):
    created = user_service.create_user(
        username=payload.username,
        password=payload.password,
        role=payload.role,
        profile_picture_url=payload.profile_picture_url,
        preferences=payload.preferences,
        acting_user=current_user,
    )
    audit_logs.attach_request_metadata(
        request,
        event="user_created",
        target_user_id=created["id"],
        target_username=created["username"],
    )
    return created


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    current_user: Dict = Depends(require_role(*ADMIN_ROLES)),
):
    update_fields = payload.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = user_service.update_user(user_id, update_fields, acting_user=current_user)
    audit_logs.attach_request_metadata(
        request,
        event="user_updated",
        target_user_id=updated["id"],
        target_username=updated["username"],
        changed_fields=sorted(update_fields.keys()),
    )
    return updated


@router.patch("/{user_id}/status", response_model=UserResponse)
def set_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    current_user: Dict = Depends(require_role(*ADMIN_ROLES)),
):
    updated = user_service.update_user(
        user_id,
        {"is_active": payload.is_active},
        acting_user=current_user,
    )
    audit_logs.attach_request_metadata(
        request,
        event="user_status_changed",
        target_user_id=updated["id"],
        target_username=updated["username"],
        is_active=updated["is_active"],
    )
    return updated


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, request: Request, current_user: Dict = Depends(require_role(*ADMIN_ROLES))):
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Users cannot delete themselves")
    deleted = user_service.delete_user(user_id, acting_user=current_user)
    audit_logs.attach_request_metadata(
        request,
        event="user_deleted",
        target_user_id=deleted["id"],
        target_username=deleted["username"],
    )
    return deleted
