from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas import UserCreate, UserListResponse, UserResponse, UserUpdate
from ..security import get_current_user, require_role
from ..services import users as user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_role("admin"))],
)


@router.get("", response_model=UserListResponse)
def list_users(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return user_service.list_users(limit=limit, offset=offset)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate):
    return user_service.create_user(
        username=payload.username,
        password=payload.password,
        role=payload.role,
        profile_picture_url=payload.profile_picture_url,
        preferences=payload.preferences,
    )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_endpoint(user_id: int, payload: UserUpdate):
    update_fields = payload.model_dump(exclude_unset=True)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    return user_service.update_user(user_id, update_fields)


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, current_user: Dict = Depends(get_current_user)):
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Users cannot delete themselves")
    return user_service.delete_user(user_id)
