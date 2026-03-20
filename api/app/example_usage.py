from __future__ import annotations

from typing import Any, Dict

from .core.enums import EntryPermission, EntryRelationType, FieldDataType, PermissionSubjectType, VisibilityLevel
from .services.entries import EntryService
from .services.metadata_schema import MetadataSchemaService
from .services.attachments import AttachmentService
from .services.permissions import PermissionService
from .services.relations import RelationService


def create_person_schema_example() -> Dict[str, Any]:
    schemas = MetadataSchemaService()
    created = schemas.create_schema(
        {
            "key": "person",
            "name": "Person",
            "description": "Dynamic person record",
            "icon": "user",
            "is_active": True,
        }
    )
    schemas.add_field(
        created["id"],
        {
            "key": "first_name",
            "label": "First Name",
            "description": "Stable technical key",
            "data_type": FieldDataType.TEXT,
            "is_required": True,
            "is_unique": False,
            "default_value": None,
            "sort_order": 10,
            "is_active": True,
            "validation_json": {"min_length": 1, "max_length": 100},
            "settings_json": {},
        },
    )
    schemas.add_field(
        created["id"],
        {
            "key": "email",
            "label": "Email",
            "description": "Unique email field",
            "data_type": FieldDataType.EMAIL,
            "is_required": False,
            "is_unique": True,
            "default_value": None,
            "sort_order": 20,
            "is_active": True,
            "validation_json": {"max_length": 255, "allow_null": True},
            "settings_json": {},
        },
    )
    return schemas.get_schema(created["id"])


def create_entry_example(schema_id: int, current_user: Dict[str, Any]) -> Dict[str, Any]:
    entries = EntryService()
    return entries.create_entry(
        {
            "schema_id": schema_id,
            "title": "Ada Lovelace",
            "status": "active",
            "visibility_level": VisibilityLevel.RESTRICTED,
            "owner_id": current_user["id"],
            "data_json": {"first_name": "Ada", "email": "ada@example.com"},
        },
        current_user=current_user,
    )


def update_entry_with_history_example(entry_id: int, current_user: Dict[str, Any]) -> Dict[str, Any]:
    entries = EntryService()
    return entries.update_entry(
        entry_id,
        {
            "data_json": {"email": "ada.lovelace@example.com"},
            "visibility_level": VisibilityLevel.INTERNAL,
            "comment": "Normalized email and relaxed visibility",
        },
        current_user=current_user,
    )


def check_access_example(entry_id: int, current_user: Dict[str, Any], target_user_id: int) -> Dict[str, Any]:
    permissions = PermissionService()
    permissions.create_permission(
        {
            "entry_id": entry_id,
            "subject_type": PermissionSubjectType.USER,
            "subject_id": str(target_user_id),
            "permission": EntryPermission.READ,
            "created_by": current_user["id"],
        }
    )
    entry = EntryService().get_entry(entry_id, current_user=current_user)
    return {
        "allowed": permissions.check_access(
            entry,
            {"id": target_user_id, "role": "user", "group_ids": []},
            EntryPermission.READ,
        )
    }


def create_relation_example(from_entry_id: int, to_entry_id: int) -> Dict[str, Any]:
    return RelationService().create_relation(
        {
            "from_entry_id": from_entry_id,
            "to_entry_id": to_entry_id,
            "relation_type": EntryRelationType.RELATED_TO,
            "sort_order": 0,
            "metadata_json": {"reason": "manual-link"},
        }
    )


def create_attachment_link_example(entry_id: int, current_user: Dict[str, Any]) -> Dict[str, Any]:
    return AttachmentService().create_attachment_link(
        entry_id=entry_id,
        file_name="case-file.pdf",
        external_url="https://drive.google.com/file/d/example/view",
        mime_type="application/pdf",
        file_size=245760,
        checksum=None,
        uploaded_by=current_user["id"],
        description="External file reference",
    )
