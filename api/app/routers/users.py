from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas import UserCreate, UserListResponse, UserResponse
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
    return user_service.create_user(payload.username, payload.password, payload.role)


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, current_user: Dict = Depends(get_current_user)):
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Users cannot delete themselves")
    return user_service.delete_user(user_id)
