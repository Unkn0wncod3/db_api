from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.enums import EntryChangeType
from ..repositories.metadata import HistoryRepository


class EntryHistoryService:
    def __init__(self):
        self.history = HistoryRepository()

    def list_history(self, entry_id: int) -> List[Dict[str, Any]]:
        return self.history.list_history(entry_id)

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
