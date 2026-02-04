import secrets
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from ..schemas import AuthLoginRequest, AuthLoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_HARDCODED_USER = {
    "username": "admin",
    "password": "c42",
    "role": "admin",
}

def _authenticate(credentials: AuthLoginRequest) -> Dict[str, str]:
    username_matches = secrets.compare_digest(credentials.username, _HARDCODED_USER["username"])
    password_matches = secrets.compare_digest(credentials.password, _HARDCODED_USER["password"])
    if not (username_matches and password_matches):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return {k: v for k, v in _HARDCODED_USER.items() if k != "password"}


@router.post("/login", response_model=AuthLoginResponse, status_code=status.HTTP_200_OK)
def login(payload: AuthLoginRequest):
    user = _authenticate(payload)
    token = secrets.token_urlsafe(32)
    return AuthLoginResponse(access_token=token, user=user)

