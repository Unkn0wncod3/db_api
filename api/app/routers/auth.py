from fastapi import APIRouter, HTTPException, status

from ..schemas import AuthLoginRequest, AuthLoginResponse, UserResponse
from ..security import create_access_token, verify_password
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
