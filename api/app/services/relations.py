from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from ..core.enums import EntryPermission
from ..core.errors import NotFoundError
from ..repositories.metadata import EntryRepository, RelationRepository, SchemaRepository
from .permissions import PermissionService


class RelationService:
    def __init__(self):
        self.entries = EntryRepository()
        self.relations = RelationRepository()
        self.schemas = SchemaRepository()
        self.permissions = PermissionService()

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

    def get_relation_tree(self, entry_id: int, current_user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        root_entry = self.entries.get_entry(entry_id)
        expanded_entry_ids: Set[int] = set()
        schema_cache: Dict[int, Dict[str, Any]] = {}
        tree = self._build_tree_node(
            entry=root_entry,
            current_user=current_user,
            via_relation=None,
            parent_entry_id=None,
            ancestor_entry_ids=set(),
            expanded_entry_ids=expanded_entry_ids,
            schema_cache=schema_cache,
        )
        return {
            "root_entry_id": entry_id,
            "tree": tree,
        }

    def _build_tree_node(
        self,
        *,
        entry: Dict[str, Any],
        current_user: Optional[Dict[str, Any]],
        via_relation: Optional[Dict[str, Any]],
        parent_entry_id: Optional[int],
        ancestor_entry_ids: Set[int],
        expanded_entry_ids: Set[int],
        schema_cache: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        entry_id = entry["id"]
        expanded_entry_ids.add(entry_id)
        next_ancestors = set(ancestor_entry_ids)
        next_ancestors.add(entry_id)

        children: List[Dict[str, Any]] = []
        for relation in self.relations.list_relations(entry_id):
            neighbor_entry_id = relation["to_entry_id"] if relation["from_entry_id"] == entry_id else relation["from_entry_id"]
            if parent_entry_id is not None and neighbor_entry_id == parent_entry_id:
                continue
            if neighbor_entry_id in next_ancestors:
                neighbor_entry = self.entries.get_entry(neighbor_entry_id)
                if self.permissions.check_access(neighbor_entry, current_user, EntryPermission.READ):
                    children.append(
                        self._reference_node(
                            entry=neighbor_entry,
                            relation=relation,
                            current_entry_id=entry_id,
                            reason="cycle",
                            schema_cache=schema_cache,
                        )
                    )
                continue

            neighbor_entry = self.entries.get_entry(neighbor_entry_id)
            if not self.permissions.check_access(neighbor_entry, current_user, EntryPermission.READ):
                continue

            if neighbor_entry_id in expanded_entry_ids:
                children.append(
                    self._reference_node(
                        entry=neighbor_entry,
                        relation=relation,
                        current_entry_id=entry_id,
                        reason="duplicate",
                        schema_cache=schema_cache,
                    )
                )
                continue

            children.append(
                self._build_tree_node(
                    entry=neighbor_entry,
                    current_user=current_user,
                    via_relation=relation,
                    parent_entry_id=entry_id,
                    ancestor_entry_ids=next_ancestors,
                    expanded_entry_ids=expanded_entry_ids,
                    schema_cache=schema_cache,
                )
            )

        children.sort(key=lambda item: (item["via_relation"]["sort_order"], item["entry"]["title"], item["entry"]["id"]))

        return {
            "entry": self._serialize_entry(entry, schema_cache=schema_cache),
            "via_relation": self._serialize_relation(via_relation, parent_entry_id=None if via_relation is None else self._relation_parent_id(via_relation, entry_id)),
            "children": children,
            "is_reference": False,
            "reference_reason": None,
        }

    def _reference_node(
        self,
        *,
        entry: Dict[str, Any],
        relation: Dict[str, Any],
        current_entry_id: int,
        reason: str,
        schema_cache: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "entry": self._serialize_entry(entry, schema_cache=schema_cache),
            "via_relation": self._serialize_relation(relation, parent_entry_id=current_entry_id),
            "children": [],
            "is_reference": True,
            "reference_reason": reason,
        }

    def _serialize_entry(self, entry: Dict[str, Any], *, schema_cache: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "id": entry["id"],
            "schema_id": entry["schema_id"],
            "schema": self._get_schema_summary(entry["schema_id"], schema_cache=schema_cache),
            "title": entry["title"],
            "status": entry["status"],
            "visibility_level": entry["visibility_level"],
            "owner_id": entry.get("owner_id"),
        }

    def _get_schema_summary(self, schema_id: int, *, schema_cache: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        schema = schema_cache.get(schema_id)
        if schema is None:
            schema = self.schemas.get_schema(schema_id)
            schema_cache[schema_id] = schema
        return {
            "id": schema["id"],
            "key": schema["key"],
            "name": schema["name"],
            "description": schema.get("description"),
            "icon": schema.get("icon"),
            "is_active": schema["is_active"],
        }

    def _serialize_relation(self, relation: Optional[Dict[str, Any]], *, parent_entry_id: Optional[int]) -> Optional[Dict[str, Any]]:
        if relation is None or parent_entry_id is None:
            return None
        direction = "outgoing" if relation["from_entry_id"] == parent_entry_id else "incoming"
        return {
            "relation_id": relation["id"],
            "from_entry_id": relation["from_entry_id"],
            "to_entry_id": relation["to_entry_id"],
            "relation_type": relation["relation_type"],
            "sort_order": relation["sort_order"],
            "metadata_json": relation.get("metadata_json") or {},
            "direction": direction,
        }

    def _relation_parent_id(self, relation: Dict[str, Any], child_entry_id: int) -> int:
        if relation["from_entry_id"] == child_entry_id:
            return relation["to_entry_id"]
        return relation["from_entry_id"]
