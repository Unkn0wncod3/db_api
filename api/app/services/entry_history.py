from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryChangeType
from ..roles import ADMIN_ROLE_SET
from ..repositories.metadata import HistoryRepository


class EntryHistoryService:
    def __init__(self):
        self.history = HistoryRepository()

    def list_history(self, entry_id: int) -> List[Dict[str, Any]]:
        return self.history.list_history(entry_id)

    def list_global_history(
        self,
        *,
        current_user: Optional[Dict[str, Any]],
        limit: int,
        offset: int,
        search: Optional[str] = None,
        schema_id: Optional[int] = None,
        entry_id: Optional[int] = None,
        changed_by: Optional[int] = None,
        change_type: Optional[str] = None,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
    ) -> Dict[str, Any]:
        result = self.history.list_global_history(
            limit=limit,
            offset=offset,
            search=search,
            schema_id=schema_id,
            entry_id=entry_id,
            changed_by=changed_by,
            change_type=change_type,
            date_from=date_from,
            date_to=date_to,
            is_admin=(current_user or {}).get("role") in ADMIN_ROLE_SET,
            user_id=(current_user or {}).get("id"),
            role=(current_user or {}).get("role"),
            group_ids=[str(group_id) for group_id in (current_user or {}).get("group_ids", [])],
        )
        return {
            "items": [self._enrich_history_item(item) for item in result["items"]],
            "limit": limit,
            "offset": offset,
            "total": result["total"],
        }

    def add_history(
        self,
        *,
        entry_id: int,
        changed_by: Optional[int],
        change_type: EntryChangeType,
        old_data_json: Optional[Dict[str, Any]],
        new_data_json: Optional[Dict[str, Any]],
        old_visibility_level: Optional[str],
        new_visibility_level: Optional[str],
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.history.add_history(
            {
                "entry_id": entry_id,
                "changed_by": changed_by,
                "change_type": change_type.value,
                "old_data_json": old_data_json,
                "new_data_json": new_data_json,
                "old_visibility_level": old_visibility_level,
                "new_visibility_level": new_visibility_level,
                "comment": comment,
            }
        )

    def _enrich_history_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(item)
        old_data = record.get("old_data_json") or {}
        new_data = record.get("new_data_json") or {}
        changed_fields = sorted(
            key
            for key in set(old_data) | set(new_data)
            if old_data.get(key) != new_data.get(key)
        )
        if record.get("old_visibility_level") != record.get("new_visibility_level"):
            changed_fields.append("visibility_level")
        record["changed_fields"] = changed_fields
        return record
