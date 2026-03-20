from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.enums import EntryPermission, PermissionSubjectType, VisibilityLevel


@dataclass(slots=True)
class EntryAccessContext:
    user_id: Optional[int]
    role: Optional[str]
    group_ids: List[str] = field(default_factory=list)


@dataclass(slots=True)
class EntryPermissionGrant:
    id: int
    entry_id: int
    subject_type: PermissionSubjectType
    subject_id: str
    permission: EntryPermission
    created_at: datetime
    created_by: Optional[int]


@dataclass(slots=True)
class EntryRecord:
    id: int
    schema_id: int
    title: str
    status: str
    visibility_level: VisibilityLevel
    owner_id: Optional[int]
    created_by: Optional[int]
    data_json: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    archived_at: Optional[datetime]
    deleted_at: Optional[datetime]
