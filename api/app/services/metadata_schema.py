from __future__ import annotations

from typing import Any, Dict, List

from ..repositories.metadata import FieldRepository, SchemaRepository


class MetadataSchemaService:
    def __init__(self):
        self.schemas = SchemaRepository()
        self.fields = FieldRepository()

    def list_schemas(self, *, include_inactive: bool = False) -> List[Dict[str, Any]]:
        return self.schemas.list_schemas(include_inactive=include_inactive)

    def get_schema(self, schema_id: int) -> Dict[str, Any]:
        schema = self.schemas.get_schema(schema_id)
        schema["fields"] = self.fields.list_fields(schema_id, include_inactive=True)
        return schema

    def create_schema(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        schema = self.schemas.create_schema(payload)
        schema["fields"] = []
        return schema

    def add_field(self, schema_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.schemas.get_schema(schema_id)
        record = dict(payload)
        record["schema_id"] = schema_id
        return self.fields.create_field(record)
