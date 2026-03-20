from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryPermission
from ..permissions.access_control import AccessControlService
from ..repositories.metadata import PermissionRepository


class PermissionService:
    def __init__(self):
        self.repo = PermissionRepository()
        self.access = AccessControlService(self.repo)

    def list_permissions(self, entry_id: int) -> List[Dict[str, Any]]:
        return self.repo.list_permissions(entry_id)

    def create_permission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(payload)
        record["subject_id"] = str(record["subject_id"])
        return self.repo.create_permission(record)

    def check_access(self, entry: Dict[str, Any], user: Optional[Dict[str, Any]], permission: EntryPermission) -> bool:
        return self.access.can_access(entry, user, permission)

    def require_access(self, entry: Dict[str, Any], user: Optional[Dict[str, Any]], permission: EntryPermission) -> None:
        self.access.require_access(entry, user, permission)
