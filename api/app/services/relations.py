from __future__ import annotations

from typing import Any, Dict, List

from ..repositories.metadata import EntryRepository, RelationRepository


class RelationService:
    def __init__(self):
        self.entries = EntryRepository()
        self.relations = RelationRepository()

    def list_relations(self, entry_id: int) -> List[Dict[str, Any]]:
        self.entries.get_entry(entry_id)
        return self.relations.list_relations(entry_id)

    def create_relation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.entries.get_entry(payload["from_entry_id"])
        self.entries.get_entry(payload["to_entry_id"])
        return self.relations.create_relation(payload)
