import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Callable, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db import get_connection

TOKEN_TTL_SECONDS = int(os.environ.get("AUTH_TOKEN_TTL_SECONDS", "14400"))
_bearer_scheme = HTTPBearer(auto_error=False)
_HASH_ITERATIONS = 120_000


def _get_secret_key() -> bytes:
    key = os.environ.get("AUTH_SECRET_KEY")
    if not key:
        raise RuntimeError("AUTH_SECRET_KEY env var is required for authentication")
    return key.encode("utf-8")


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _HASH_ITERATIONS)
    return _b64_encode(salt + digest)


def verify_password(password: str, encoded: str) -> bool:
    try:
        data = _b64_decode(encoded)
    except Exception:
        return False
    if len(data) < 16:
        return False
    salt, stored_hash = data[:16], data[16:]
    new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _HASH_ITERATIONS)
    return hmac.compare_digest(stored_hash, new_hash)


def create_access_token(user: Dict[str, Any]) -> str:
    payload = {
        "sub": user["id"],
        "role": user["role"],
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64_encode(payload_bytes)
    secret = _get_secret_key()
    signature = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    signature_b64 = _b64_encode(signature)
    return f"{payload_b64}.{signature_b64}"


def _decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload_b64, signature_b64 = token.split(".")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    secret = _get_secret_key()
    expected_signature = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64_encode(expected_signature), signature_b64):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
    try:
        payload = json.loads(_b64_decode(payload_b64))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> Dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
    token_data = _decode_access_token(credentials.credentials)

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, role, is_active, created_at, updated_at FROM users WHERE id=%s;",
            (token_data["sub"],),
        )
        user = cur.fetchone()

    if not user or not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    if user["role"] != token_data.get("role"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token role mismatch")
    return user


def require_role(*roles: str) -> Callable:
    if not roles:
        raise ValueError("At least one role must be provided")

    def dependency(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
