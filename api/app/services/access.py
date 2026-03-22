from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.enums import EntryPermission
from .permissions import PermissionService


class EntryAccessService:
    def __init__(self):
        self.permissions = PermissionService()

    def get_access_map(self, entry: Dict[str, Any], current_user: Optional[Dict[str, Any]]) -> Dict[str, bool]:
        return self.permissions.get_access_map(entry, current_user)

    def check_access(
        self,
        entry: Dict[str, Any],
        current_user: Optional[Dict[str, Any]],
        permission: EntryPermission,
    ) -> bool:
        access_map = self.get_access_map(entry, current_user)
        return access_map[permission.value]
