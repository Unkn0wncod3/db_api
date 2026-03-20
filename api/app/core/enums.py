from __future__ import annotations

from enum import StrEnum


class FieldDataType(StrEnum):
    TEXT = "text"
    LONG_TEXT = "long_text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    URL = "url"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    REFERENCE = "reference"
    FILE = "file"
    JSON = "json"


class VisibilityLevel(StrEnum):
    PRIVATE = "private"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    PUBLIC = "public"


class PermissionSubjectType(StrEnum):
    USER = "user"
    ROLE = "role"
    GROUP = "group"


class EntryPermission(StrEnum):
    READ = "read"
    VIEW_HISTORY = "view_history"
    EDIT = "edit"
    EDIT_STATUS = "edit_status"
    EDIT_VISIBILITY = "edit_visibility"
    MANAGE_RELATIONS = "manage_relations"
    MANAGE_ATTACHMENTS = "manage_attachments"
    MANAGE_PERMISSIONS = "manage_permissions"
    DELETE = "delete"
    MANAGE = "manage"


class EntryRelationType(StrEnum):
    BELONGS_TO = "belongs_to"
    PARENT_OF = "parent_of"
    REFERENCES = "references"
    ASSIGNED_TO = "assigned_to"
    CONTAINS = "contains"
    RELATED_TO = "related_to"


class EntryChangeType(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    VISIBILITY_CHANGED = "visibility_changed"
    STATUS_CHANGED = "status_changed"
    ARCHIVED = "archived"
    DELETED = "deleted"
