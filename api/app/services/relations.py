from __future__ import annotations

from typing import Any, Dict, List

from ..core.errors import NotFoundError
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

    def update_relation(self, entry_id: int, relation_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.entries.get_entry(entry_id)
        relation = self.relations.get_relation(relation_id)
        if relation["from_entry_id"] != entry_id and relation["to_entry_id"] != entry_id:
            raise NotFoundError("Relation not found for entry")
        updates = dict(payload)
        if "to_entry_id" in updates and updates["to_entry_id"] is not None:
            self.entries.get_entry(updates["to_entry_id"])
        return self.relations.update_relation(relation_id, updates)

    def delete_relation(self, entry_id: int, relation_id: int) -> Dict[str, Any]:
        self.entries.get_entry(entry_id)
        relation = self.relations.get_relation(relation_id)
        if relation["from_entry_id"] != entry_id and relation["to_entry_id"] != entry_id:
            raise NotFoundError("Relation not found for entry")
        return self.relations.delete_relation(relation_id)
