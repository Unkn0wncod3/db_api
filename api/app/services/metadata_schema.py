from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryPermission
from ..core.errors import ValidationError
from ..repositories.metadata import EntryRepository, FieldRepository, SchemaRepository
from .permissions import PermissionService


class MetadataSchemaService:
    def __init__(self):
        self.schemas = SchemaRepository()
        self.fields = FieldRepository()
        self.entries = EntryRepository()
        self.permissions = PermissionService()

    def list_schemas(self, *, include_inactive: bool = False) -> List[Dict[str, Any]]:
        return self.schemas.list_schemas(include_inactive=include_inactive)

    def get_schema(self, schema_id: int) -> Dict[str, Any]:
        schema = self.schemas.get_schema(schema_id)
        schema["fields"] = self.fields.list_fields(schema_id, include_inactive=True)
        return schema

    def get_schema_entries(self, schema_id: int, *, current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        schema = self.get_schema(schema_id)
        rows = self.entries.list_entries(schema_id=schema_id)
        visible_entries = []
        for row in rows:
            if not self.permissions.check_access(row, current_user, EntryPermission.READ):
                continue
            entry = dict(row)
            entry["access"] = {
                permission.value: self.permissions.check_access(row, current_user, permission)
                for permission in EntryPermission
            }
            visible_entries.append(entry)
        return {
            "schema": schema,
            "entries": visible_entries,
        }

    def create_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        schema = self.schemas.create_schema(payload)
        schema["fields"] = []
        return schema

    def add_field(self, schema_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.schemas.get_schema(schema_id)
        record = dict(payload)
        record["schema_id"] = schema_id
        return self.fields.create_field(record)

    def list_fields(self, schema_id: int, *, include_inactive: bool = True) -> List[Dict[str, Any]]:
        self.schemas.get_schema(schema_id)
        return self.fields.list_fields(schema_id, include_inactive=include_inactive)

    def get_field(self, schema_id: int, field_id: int) -> Dict[str, Any]:
        self.schemas.get_schema(schema_id)
        return self.fields.get_field(schema_id, field_id)

    def update_field(self, schema_id: int, field_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.schemas.get_schema(schema_id)
        if not payload:
            raise ValidationError([{"field": "_request", "message": "No fields to update"}])
        return self.fields.update_field(schema_id, field_id, payload)

    def delete_field(self, schema_id: int, field_id: int) -> Dict[str, Any]:
        self.schemas.get_schema(schema_id)
        return self.fields.delete_field(schema_id, field_id)
