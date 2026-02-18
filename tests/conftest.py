from datetime import datetime

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from api.app.main import app
from api.app.roles import READ_ROLES
from api.app.security import get_current_user


def _test_current_user(request: Request):
    valid_roles = set(READ_ROLES)
    role = request.headers.get("X-Test-Role", "head_admin")
    if role not in valid_roles:
        role = "head_admin"
    now = datetime.utcnow()
    return {
        "id": 999,
        "username": f"test_{role}",
        "role": role,
        "is_active": True,
        "created_at": now,
        "updated_at": None,
    }


@pytest.fixture(scope="session")
def client():
    app.dependency_overrides[get_current_user] = _test_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_current_user, None)
