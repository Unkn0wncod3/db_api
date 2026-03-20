from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryPermission
from ..repositories.metadata import EntryRepository, SchemaRepository
from .permissions import PermissionService


class DashboardService:
    def __init__(self):
        self.entries = EntryRepository()
        self.schemas = SchemaRepository()
        self.permissions = PermissionService()

    def get_overview(self, *, current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        schema_rows = self.schemas.list_schemas(include_inactive=True)
        schema_map = {row["id"]: row for row in schema_rows}

        visible_entries = [
            row
            for row in self.entries.list_entries()
            if self.permissions.check_access(row, current_user, EntryPermission.READ)
        ]

        latest_created = self._to_entry_summary_list(
            sorted(
                visible_entries,
                key=lambda row: (row["created_at"], row["id"]),
                reverse=True,
            )[:5],
            schema_map,
        )
        latest_updated = self._to_entry_summary_list(
            sorted(
                visible_entries,
                key=lambda row: ((row.get("updated_at") or row["created_at"]), row["id"]),
                reverse=True,
            )[:5],
            schema_map,
        )

        per_schema: Dict[int, Dict[str, Any]] = {}
        for entry in visible_entries:
            schema = schema_map.get(entry["schema_id"])
            if not schema:
                continue
            stats = per_schema.setdefault(
                entry["schema_id"],
                {
                    "schema_id": schema["id"],
                    "schema_key": schema["key"],
                    "schema_name": schema["name"],
                    "icon": schema.get("icon"),
                    "total_entries": 0,
                    "last_created_at": None,
                    "last_updated_at": None,
                },
            )
            stats["total_entries"] += 1
            created_at = entry["created_at"]
            updated_at = entry.get("updated_at") or created_at
            if stats["last_created_at"] is None or created_at > stats["last_created_at"]:
                stats["last_created_at"] = created_at
            if stats["last_updated_at"] is None or updated_at > stats["last_updated_at"]:
                stats["last_updated_at"] = updated_at

        totals_per_schema = sorted(
            per_schema.values(),
            key=lambda row: (-row["total_entries"], row["schema_name"], row["schema_id"]),
        )

        return {
            "total_entries": len(visible_entries),
            "latest_created": latest_created,
            "latest_updated": latest_updated,
            "totals_per_schema": totals_per_schema,
        }

    def _to_entry_summary_list(
        self,
        entries: List[Dict[str, Any]],
        schema_map: Dict[int, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for entry in entries:
            schema = schema_map.get(entry["schema_id"])
            if not schema:
                continue
            result.append(
                {
                    "id": entry["id"],
                    "schema_id": entry["schema_id"],
                    "schema_key": schema["key"],
                    "schema_name": schema["name"],
                    "title": entry["title"],
                    "status": entry["status"],
                    "visibility_level": entry["visibility_level"],
                    "owner_id": entry.get("owner_id"),
                    "created_at": entry["created_at"],
                    "updated_at": entry.get("updated_at"),
                }
            )
        return result
