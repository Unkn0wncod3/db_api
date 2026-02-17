from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from ..schemas import AuthLoginRequest, AuthLoginResponse, UserResponse, UserUpdate
from ..security import create_access_token, get_current_user, verify_password
from ..services import users as user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthLoginResponse, status_code=status.HTTP_200_OK)
def login(payload: AuthLoginRequest):
    db_user = user_service.get_user_by_username(payload.username, include_secret=True)
    if not db_user or not db_user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    if not verify_password(payload.password, db_user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    token = create_access_token(db_user)
    user_payload = UserResponse(
        id=db_user["id"],
        username=db_user["username"],
        role=db_user["role"],
        is_active=db_user["is_active"],
        profile_picture_url=db_user.get("profile_picture_url"),
        preferences=db_user.get("preferences") or {},
        created_at=db_user["created_at"],
        updated_at=db_user.get("updated_at"),
    )
    return AuthLoginResponse(access_token=token, user=user_payload)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def read_current_user(current_user: Dict = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_current_user(payload: UserUpdate, current_user: Dict = Depends(get_current_user)):
    allowed_fields = {}
    if payload.username is not None:
        allowed_fields["username"] = payload.username
    if payload.password is not None:
        allowed_fields["password"] = payload.password
    if payload.profile_picture_url is not None:
        allowed_fields["profile_picture_url"] = payload.profile_picture_url
    if payload.preferences is not None:
        allowed_fields["preferences"] = payload.preferences

    if not allowed_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes supplied")

    return user_service.update_user(current_user["id"], allowed_fields)
