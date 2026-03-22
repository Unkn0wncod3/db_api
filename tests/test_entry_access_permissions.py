from api.app.permissions.access_control import AccessControlService
from api.app.security import create_access_token


class _FakePermissionRepository:
    def __init__(self, grants):
        self._grants = list(grants)

    def list_permissions(self, entry_id: int):
        return [grant for grant in self._grants if grant["entry_id"] == entry_id]


def _entry(*, entry_id: int = 1, visibility_level: str = "private", owner_id=None):
    return {"id": entry_id, "visibility_level": visibility_level, "owner_id": owner_id}


def test_explicit_user_permission_grants_access():
    service = AccessControlService(
        _FakePermissionRepository(
            [{"entry_id": 1, "subject_type": "user", "subject_id": "123", "permission": "edit"}]
        )
    )

    access = service.get_access_map(_entry(), {"id": 123, "role": "reader"})

    assert access["read"] is True
    assert access["edit"] is True
    assert access["delete"] is False


def test_explicit_role_permission_grants_access():
    service = AccessControlService(
        _FakePermissionRepository(
            [{"entry_id": 1, "subject_type": "role", "subject_id": "editor", "permission": "read"}]
        )
    )

    access = service.get_access_map(_entry(), {"id": 77, "role": "editor"})

    assert access["read"] is True
    assert access["edit"] is False


def test_manage_permission_implies_full_entry_access():
    service = AccessControlService(
        _FakePermissionRepository(
            [{"entry_id": 1, "subject_type": "user", "subject_id": "123", "permission": "manage"}]
        )
    )

    access = service.get_access_map(_entry(), {"id": 123, "role": "reader"})

    assert all(access.values())


def test_no_permission_leaves_private_entry_inaccessible():
    service = AccessControlService(_FakePermissionRepository([]))

    access = service.get_access_map(_entry(), {"id": 123, "role": "reader"})

    assert access["read"] is False
    assert access["edit"] is False
    assert access["manage"] is False


def test_entry_grant_extends_global_base_access_without_revoking_it():
    service = AccessControlService(
        _FakePermissionRepository(
            [{"entry_id": 1, "subject_type": "role", "subject_id": "reader", "permission": "edit"}]
        )
    )

    access = service.get_access_map(_entry(visibility_level="internal"), {"id": 123, "role": "reader"})

    assert access["read"] is True
    assert access["edit"] is True
    assert access["manage"] is False


def test_bundle_and_access_endpoint_use_consistent_role_grant_logic(client):
    from api.app.db import get_connection

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, username, password_hash, role, is_active, preferences)
            VALUES
                (999, 'access_admin', 'test-hash', 'head_admin', TRUE, '{}'::jsonb),
                (1001, 'bundle_reader', 'test-hash', 'reader', TRUE, '{}'::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                username = EXCLUDED.username,
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                preferences = EXCLUDED.preferences;
            """
        )
        conn.commit()

    schema_resp = client.post(
        "/schemas",
        json={
            "key": "entry_access_case",
            "name": "Entry Access Case",
            "description": "Schema for effective access tests",
            "icon": "shield",
            "is_active": True,
        },
    )
    assert schema_resp.status_code == 201
    schema_id = schema_resp.json()["id"]

    entry_resp = client.post(
        "/entries",
        json={
            "schema_id": schema_id,
            "title": "Protected Entry",
            "status": "draft",
            "visibility_level": "private",
            "data_json": {},
        },
    )
    assert entry_resp.status_code == 201
    entry_id = entry_resp.json()["id"]

    permission_resp = client.post(
        f"/entries/{entry_id}/permissions",
        json={
            "subject_type": "role",
            "subject_id": "reader",
            "permission": "edit",
        },
    )
    assert permission_resp.status_code == 201

    reader_token = create_access_token({"id": 1001, "role": "reader"})
    reader_headers = {"Authorization": f"Bearer {reader_token}"}

    bundle_resp = client.get(f"/entries/{entry_id}/bundle", headers=reader_headers)
    assert bundle_resp.status_code == 200
    bundle_access = bundle_resp.json()["access"]

    read_check = client.get(f"/entries/{entry_id}/access/read", headers={"X-Test-Role": "reader"})
    assert read_check.status_code == 200
    assert read_check.json()["allowed"] == bundle_access["read"]

    edit_check = client.get(f"/entries/{entry_id}/access/edit", headers={"X-Test-Role": "reader"})
    assert edit_check.status_code == 200
    assert edit_check.json()["allowed"] == bundle_access["edit"]
