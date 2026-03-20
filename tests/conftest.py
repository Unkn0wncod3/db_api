from datetime import datetime
from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from api.app.db import get_connection
from api.app.main import app
from api.app.roles import READ_ROLES
from api.app.security import get_current_user


def _test_current_user(request: Request):
    valid_roles = set(READ_ROLES)
    role = request.headers.get("X-Test-Role", "head_admin")
    if role not in valid_roles:
        role = "head_admin"
    now = datetime.utcnow()
    user = {
        "id": 999,
        "username": f"test_{role}",
        "role": role,
        "is_active": True,
        "created_at": now,
        "updated_at": None,
    }
    request.state.current_user = user
    return user


def _initialize_test_schema() -> None:
    drop_sql = (Path(__file__).resolve().parents[1] / "db" / "drop_all.sql").read_text(encoding="utf-8")
    init_sql = Path(__file__).resolve().parents[1] / "db" / "init.sql"
    sql = init_sql.read_text(encoding="utf-8")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(drop_sql)
        conn.commit()
        cur.execute(sql)
        conn.commit()


@pytest.fixture(scope="session")
def client():
    _initialize_test_schema()
    app.dependency_overrides[get_current_user] = _test_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_current_user, None)
