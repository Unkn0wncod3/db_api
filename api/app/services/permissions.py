from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryPermission, PermissionSubjectType
from ..core.errors import NotFoundError, ValidationError
from ..permissions.access_control import AccessControlService
from ..repositories.metadata import EntryRepository
from ..repositories.metadata import PermissionRepository


class PermissionService:
    def __init__(self):
        self.entries = EntryRepository()
        self.repo = PermissionRepository()
        self.access = AccessControlService(self.repo)

    def list_permissions(self, entry_id: int) -> List[Dict[str, Any]]:
        return self.repo.list_permissions(entry_id)

    def create_permission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        self._validate_subject_type(record.get("subject_type"))
        record["subject_id"] = str(record["subject_id"])
        return self.repo.create_permission(record)

    def update_permission(self, entry_id: int, permission_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        self.entries.get_entry(entry_id)
        permission = self.repo.get_permission(permission_id)
        if permission["entry_id"] != entry_id:
            raise NotFoundError("Permission not found for entry")

        if not updates:
            raise ValidationError([{"field": "_request", "message": "No fields to update"}])

        payload = dict(updates)
        if "subject_type" in payload:
            self._validate_subject_type(payload.get("subject_type"))
        if "subject_id" in payload and payload["subject_id"] is not None:
            payload["subject_id"] = str(payload["subject_id"])
        return self.repo.update_permission(permission_id, payload)

    def delete_permission(self, entry_id: int, permission_id: int) -> Dict[str, Any]:
        self.entries.get_entry(entry_id)
        permission = self.repo.get_permission(permission_id)
        if permission["entry_id"] != entry_id:
            raise NotFoundError("Permission not found for entry")
        return self.repo.delete_permission(permission_id)

    def check_access(self, entry: Dict[str, Any], user: Optional[Dict[str, Any]], permission: EntryPermission) -> bool:
        return self.access.can_access(entry, user, permission)

    def get_access_map(self, entry: Dict[str, Any], user: Optional[Dict[str, Any]]) -> Dict[str, bool]:
        return self.access.get_access_map(entry, user)

    def require_access(self, entry: Dict[str, Any], user: Optional[Dict[str, Any]], permission: EntryPermission) -> None:
        self.access.require_access(entry, user, permission)

    def _validate_subject_type(self, subject_type: Any) -> None:
        if subject_type == PermissionSubjectType.GROUP or subject_type == PermissionSubjectType.GROUP.value:
            raise ValidationError(
                [{"field": "subject_type", "message": "Group subjects are not supported until a group model exists"}]
            )
