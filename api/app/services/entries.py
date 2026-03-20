from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryChangeType, EntryPermission
from ..core.errors import ValidationError
from ..repositories.metadata import EntryRepository, FieldRepository, SchemaRepository, ensure_unique_field_value
from ..validation.entries import validate_entry_payload
from .attachments import AttachmentService
from .entry_history import EntryHistoryService
from .permissions import PermissionService
from .relations import RelationService


class EntryService:
    def __init__(self):
        self.schemas = SchemaRepository()
        self.fields = FieldRepository()
        self.entries = EntryRepository()
        self.history = EntryHistoryService()
        self.permissions = PermissionService()
        self.relations = RelationService()
        self.attachments = AttachmentService()

    def list_entries(
        self,
        *,
        current_user: Optional[Dict[str, Any]],
        schema_id: Optional[int] = None,
        owner_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        rows = self.entries.list_entries(schema_id=schema_id, owner_id=owner_id)
        return [row for row in rows if self.permissions.check_access(row, current_user, EntryPermission.READ)]

    def get_entry(
        self,
        entry_id: int,
        *,
        current_user: Optional[Dict[str, Any]],
        permission: EntryPermission = EntryPermission.READ,
    ) -> Dict[str, Any]:
        row = self.entries.get_entry(entry_id)
        self.permissions.require_access(row, current_user, permission)
        return row

    def get_entry_bundle(
        self,
        entry_id: int,
        *,
        current_user: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        entry = self.get_entry(entry_id, current_user=current_user, permission=EntryPermission.READ)
        access = self._build_access_map(entry, current_user)
        return {
            "entry": entry,
            "schema": self._get_schema_with_fields(entry["schema_id"]),
            "access": access,
            "history": self.history.list_history(entry_id) if access[EntryPermission.VIEW_HISTORY.value] else [],
            "relations": self.relations.list_relations(entry_id),
            "attachments": self.attachments.list_attachments(entry_id),
            "permissions": self.permissions.list_permissions(entry_id) if access[EntryPermission.MANAGE_PERMISSIONS.value] else [],
        }

    def create_entry(self, payload: Dict[str, Any], *, current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        schema = self.schemas.get_schema(payload["schema_id"])
        fields = self.fields.list_fields(schema["id"])
        validated_data = validate_entry_payload(fields=fields, data=payload.get("data_json") or {}, partial=False)
        self._ensure_unique_fields(schema["id"], fields, validated_data)

        actor_id = (current_user or {}).get("id")
        entry = self.entries.create_entry(
            {
                "schema_id": schema["id"],
                "title": payload["title"],
                "status": payload.get("status", "draft"),
                "visibility_level": payload["visibility_level"],
                "owner_id": payload.get("owner_id") or actor_id,
                "created_by": actor_id,
                "data_json": validated_data,
                "archived_at": payload.get("archived_at"),
                "deleted_at": payload.get("deleted_at"),
            }
        )
        self.history.add_history(
            entry_id=entry["id"],
            changed_by=actor_id,
            change_type=EntryChangeType.CREATED,
            old_data_json=None,
            new_data_json=entry["data_json"],
            old_visibility_level=None,
            new_visibility_level=entry["visibility_level"],
            comment="Entry created",
        )
        return entry

    def update_entry(
        self,
        entry_id: int,
        payload: Dict[str, Any],
        *,
        current_user: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        existing = self.entries.get_entry(entry_id)
        for permission in self._permissions_for_update(payload):
            self.permissions.require_access(existing, current_user, permission)
        fields = self.fields.list_fields(existing["schema_id"])
        old_data = existing.get("data_json") or {}
        new_data = dict(old_data)
        update_fields: Dict[str, Any] = {}

        if "data_json" in payload and payload["data_json"] is not None:
            validated = validate_entry_payload(fields=fields, data=payload["data_json"], partial=True)
            new_data.update(validated)
            self._ensure_unique_fields(existing["schema_id"], fields, new_data, exclude_entry_id=entry_id)
            update_fields["data_json"] = new_data

        for key in ("title", "status", "visibility_level", "owner_id", "archived_at", "deleted_at"):
            if key in payload and payload[key] is not None:
                update_fields[key] = payload[key]

        if not update_fields:
            raise ValidationError([{"field": "_request", "message": "No fields to update"}])

        updated = self.entries.update_entry(entry_id, update_fields)
        change_type = EntryChangeType.UPDATED
        if existing["visibility_level"] != updated["visibility_level"]:
            change_type = EntryChangeType.VISIBILITY_CHANGED
        self.history.add_history(
            entry_id=updated["id"],
            changed_by=(current_user or {}).get("id"),
            change_type=change_type,
            old_data_json=old_data,
            new_data_json=updated["data_json"],
            old_visibility_level=existing["visibility_level"],
            new_visibility_level=updated["visibility_level"],
            comment=payload.get("comment"),
        )
        return updated

    def _permissions_for_update(self, payload: Dict[str, Any]) -> List[EntryPermission]:
        required: List[EntryPermission] = []
        if any(key in payload and payload[key] is not None for key in ("title", "data_json")):
            required.append(EntryPermission.EDIT)
        if "status" in payload and payload["status"] is not None:
            required.append(EntryPermission.EDIT_STATUS)
        if "visibility_level" in payload and payload["visibility_level"] is not None:
            required.append(EntryPermission.EDIT_VISIBILITY)
        if any(key in payload and payload[key] is not None for key in ("owner_id", "archived_at", "deleted_at")):
            required.append(EntryPermission.MANAGE)
        if not required:
            required.append(EntryPermission.EDIT)
        return required

    def list_history(self, entry_id: int, *, current_user: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.get_entry(entry_id, current_user=current_user, permission=EntryPermission.VIEW_HISTORY)
        return self.history.list_history(entry_id)

    def _ensure_unique_fields(
        self,
        schema_id: int,
        fields: List[Dict[str, Any]],
        data_json: Dict[str, Any],
        *,
        exclude_entry_id: Optional[int] = None,
    ) -> None:
        for field in fields:
            if not field.get("is_unique"):
                continue
            field_key = field["key"]
            if field_key not in data_json or data_json[field_key] is None:
                continue
            ensure_unique_field_value(schema_id, field_key, data_json[field_key], exclude_entry_id=exclude_entry_id)

    def _build_access_map(self, entry: Dict[str, Any], current_user: Optional[Dict[str, Any]]) -> Dict[str, bool]:
        return {
            permission.value: self.permissions.check_access(entry, current_user, permission)
            for permission in EntryPermission
        }

    def _get_schema_with_fields(self, schema_id: int) -> Dict[str, Any]:
        schema = self.schemas.get_schema(schema_id)
        schema["fields"] = self.fields.list_fields(schema_id, include_inactive=True)
        return schema
