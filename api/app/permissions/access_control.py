from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryPermission, PermissionSubjectType, VisibilityLevel
from ..core.errors import ForbiddenError
from ..models.metadata import EntryAccessContext
from ..repositories.metadata import PermissionRepository
from ..roles import ADMIN_ROLE_SET

_PERMISSION_IMPLICATIONS = {
    EntryPermission.READ: {EntryPermission.READ},
    EntryPermission.VIEW_HISTORY: {EntryPermission.READ, EntryPermission.VIEW_HISTORY},
    EntryPermission.EDIT: {EntryPermission.READ, EntryPermission.EDIT},
    EntryPermission.EDIT_STATUS: {EntryPermission.READ, EntryPermission.EDIT_STATUS},
    EntryPermission.EDIT_VISIBILITY: {EntryPermission.READ, EntryPermission.EDIT_VISIBILITY},
    EntryPermission.MANAGE_RELATIONS: {EntryPermission.READ, EntryPermission.MANAGE_RELATIONS},
    EntryPermission.MANAGE_ATTACHMENTS: {EntryPermission.READ, EntryPermission.MANAGE_ATTACHMENTS},
    EntryPermission.MANAGE_PERMISSIONS: {EntryPermission.READ, EntryPermission.MANAGE_PERMISSIONS},
    EntryPermission.DELETE: {EntryPermission.READ, EntryPermission.DELETE},
    EntryPermission.MANAGE: set(EntryPermission),
}


class AccessControlService:
    def __init__(self, permission_repository: Optional[PermissionRepository] = None):
        self.permission_repository = permission_repository or PermissionRepository()

    def build_context(self, user: Optional[Dict[str, Any]]) -> EntryAccessContext:
        group_ids = user.get("group_ids", []) if user else []
        return EntryAccessContext(
            user_id=(user or {}).get("id"),
            role=(user or {}).get("role"),
            group_ids=[str(group_id) for group_id in group_ids],
        )

    def can_access(self, entry: Dict[str, Any], user: Optional[Dict[str, Any]], permission: EntryPermission) -> bool:
        context = self.build_context(user)
        if context.role in ADMIN_ROLE_SET:
            return True
        if permission == EntryPermission.READ and self._is_visible(entry, context):
            return True
        if context.user_id is not None and entry.get("owner_id") == context.user_id:
            return True
        grants = self.permission_repository.list_permissions(entry["id"])
        return self._has_matching_grant(grants, context, permission)

    def require_access(self, entry: Dict[str, Any], user: Optional[Dict[str, Any]], permission: EntryPermission) -> None:
        if not self.can_access(entry, user, permission):
            raise ForbiddenError("Access denied for requested entry")

    def _is_visible(self, entry: Dict[str, Any], context: EntryAccessContext) -> bool:
        level = VisibilityLevel(entry["visibility_level"])
        if level == VisibilityLevel.PUBLIC:
            return True
        if level == VisibilityLevel.INTERNAL:
            return context.user_id is not None
        return False

    def _has_matching_grant(
        self,
        grants: List[Dict[str, Any]],
        context: EntryAccessContext,
        requested_permission: EntryPermission,
    ) -> bool:
        for grant in grants:
            if not self._subject_matches(grant, context):
                continue
            granted_permission = EntryPermission(grant["permission"])
            if requested_permission in _PERMISSION_IMPLICATIONS[granted_permission]:
                return True
        return False

    def _subject_matches(self, grant: Dict[str, Any], context: EntryAccessContext) -> bool:
        subject_type = PermissionSubjectType(grant["subject_type"])
        subject_id = str(grant["subject_id"])
        if subject_type == PermissionSubjectType.USER:
            return context.user_id is not None and str(context.user_id) == subject_id
        if subject_type == PermissionSubjectType.ROLE:
            return context.role is not None and context.role == subject_id
        if subject_type == PermissionSubjectType.GROUP:
            return subject_id in context.group_ids
        return False
