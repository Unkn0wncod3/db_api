from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.errors import NotFoundError, ValidationError
from ..repositories.metadata import AttachmentRepository, EntryRepository


class AttachmentService:
    def __init__(self):
        self.entries = EntryRepository()
        self.attachments = AttachmentRepository()

    def list_attachments(self, entry_id: int) -> List[Dict[str, Any]]:
        self.entries.get_entry(entry_id)
        return self.attachments.list_attachments(entry_id)

    def create_attachment_link(
        self,
        *,
        entry_id: int,
        file_name: str,
        external_url: str,
        mime_type: Optional[str],
        file_size: int,
        checksum: Optional[str],
        uploaded_by: Optional[int],
        description: Optional[str],
    ) -> Dict[str, Any]:
        self.entries.get_entry(entry_id)
        return self.attachments.create_attachment(
            {
                "entry_id": entry_id,
                "file_name": file_name,
                "stored_path": external_url,
                "mime_type": mime_type,
                "file_size": file_size,
                "checksum": checksum or external_url,
                "uploaded_by": uploaded_by,
                "description": description,
            }
        )

    def update_attachment_link(self, entry_id: int, attachment_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        self.entries.get_entry(entry_id)
        attachment = self.attachments.get_attachment(attachment_id)
        if attachment["entry_id"] != entry_id:
            raise NotFoundError("Attachment not found for entry")

        if not updates:
            raise ValidationError([{"field": "_request", "message": "No fields to update"}])

        payload = dict(updates)
        if "external_url" in payload:
            payload["stored_path"] = str(payload.pop("external_url"))
            payload["checksum"] = payload.get("checksum") or payload["stored_path"]
        return self.attachments.update_attachment(attachment_id, payload)

    def delete_attachment(self, entry_id: int, attachment_id: int) -> Dict[str, Any]:
        self.entries.get_entry(entry_id)
        attachment = self.attachments.get_attachment(attachment_id)
        if attachment["entry_id"] != entry_id:
            raise NotFoundError("Attachment not found for entry")
        return self.attachments.delete_attachment(attachment_id)
