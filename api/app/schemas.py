from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .core.enums import (
    EntryChangeType,
    EntryPermission,
    EntryRelationType,
    FieldDataType,
    PermissionSubjectType,
    VisibilityLevel,
)


class FieldDefinitionBase(BaseModel):
    key: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    data_type: FieldDataType
    is_required: bool = False
    is_unique: bool = False
    default_value: Optional[Any] = None
    sort_order: int = 0
    is_active: bool = True
    validation_json: Dict[str, Any] = Field(default_factory=dict)
    settings_json: Dict[str, Any] = Field(default_factory=dict)


class FieldDefinitionCreate(FieldDefinitionBase):
    pass


class FieldDefinitionUpdate(BaseModel):
    key: Optional[str] = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    label: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = None
    data_type: Optional[FieldDataType] = None
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    default_value: Optional[Any] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    validation_json: Optional[Dict[str, Any]] = None
    settings_json: Optional[Dict[str, Any]] = None


class FieldDefinitionResponse(FieldDefinitionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schema_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class MetadataSchemaBase(BaseModel):
    key: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=64)
    is_active: bool = True


class MetadataSchemaCreate(MetadataSchemaBase):
    pass


class MetadataSchemaResponse(MetadataSchemaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    fields: List[FieldDefinitionResponse] = Field(default_factory=list)


class EntryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="draft", min_length=1, max_length=64)
    visibility_level: VisibilityLevel = VisibilityLevel.PRIVATE
    owner_id: Optional[int] = None
    data_json: Dict[str, Any] = Field(default_factory=dict)


class EntryCreate(EntryBase):
    schema_id: int
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class EntryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[str] = Field(default=None, min_length=1, max_length=64)
    visibility_level: Optional[VisibilityLevel] = None
    owner_id: Optional[int] = None
    data_json: Optional[Dict[str, Any]] = None
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    comment: Optional[str] = Field(default=None, max_length=500)


class EntryResponse(EntryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    schema_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class EntryRelationCreate(BaseModel):
    to_entry_id: int
    relation_type: EntryRelationType = EntryRelationType.RELATED_TO
    sort_order: int = 0
    metadata_json: Dict[str, Any] = Field(default_factory=dict)


class EntryHistoryRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_id: int
    changed_by: Optional[int] = None
    change_type: EntryChangeType
    old_data_json: Dict[str, Any] = Field(default_factory=dict)
    new_data_json: Dict[str, Any] = Field(default_factory=dict)
    old_visibility_level: Optional[VisibilityLevel] = None
    new_visibility_level: Optional[VisibilityLevel] = None
    changed_at: datetime
    comment: Optional[str] = None


class EntryRelationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_entry_id: int
    to_entry_id: int
    relation_type: EntryRelationType
    sort_order: int
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_id: int
    file_name: str
    stored_path: str
    mime_type: Optional[str] = None
    file_size: int
    checksum: str
    uploaded_by: Optional[int] = None
    uploaded_at: datetime
    description: Optional[str] = None


class EntryPermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_id: int
    subject_type: PermissionSubjectType
    subject_id: str
    permission: EntryPermission
    created_at: datetime
    created_by: Optional[int] = None


class AttachmentLinkCreate(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    external_url: HttpUrl
    mime_type: Optional[str] = Field(default=None, max_length=255)
    file_size: int = Field(default=0, ge=0)
    checksum: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None


class EntryPermissionCreate(BaseModel):
    subject_type: PermissionSubjectType
    subject_id: str
    permission: EntryPermission


class AccessCheckResponse(BaseModel):
    entry_id: int
    permission: EntryPermission
    allowed: bool


class EntryWithAccessResponse(EntryResponse):
    access: Dict[str, bool] = Field(default_factory=dict)


class SchemaEntriesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_definition: MetadataSchemaResponse = Field(validation_alias="schema", serialization_alias="schema")
    entries: List[EntryWithAccessResponse] = Field(default_factory=list)


class DashboardEntrySummary(BaseModel):
    id: int
    schema_id: int
    schema_key: str
    schema_name: str
    title: str
    status: str
    visibility_level: VisibilityLevel
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class DashboardSchemaTotal(BaseModel):
    schema_id: int
    schema_key: str
    schema_name: str
    icon: Optional[str] = None
    total_entries: int
    last_created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None


class DashboardOverviewResponse(BaseModel):
    total_entries: int
    latest_created: List[DashboardEntrySummary] = Field(default_factory=list)
    latest_updated: List[DashboardEntrySummary] = Field(default_factory=list)
    totals_per_schema: List[DashboardSchemaTotal] = Field(default_factory=list)


class EntryBundleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    entry: EntryResponse
    schema_definition: MetadataSchemaResponse = Field(validation_alias="schema", serialization_alias="schema")
    access: Dict[str, bool] = Field(default_factory=dict)
    history: List[EntryHistoryRecord] = Field(default_factory=list)
    relations: List[EntryRelationResponse] = Field(default_factory=list)
    attachments: List[AttachmentResponse] = Field(default_factory=list)
    permissions: List[EntryPermissionResponse] = Field(default_factory=list)


Role = Literal["head_admin", "admin", "manager", "editor", "reader"]


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    role: Role = "reader"
    profile_picture_url: Optional[str] = Field(default=None, max_length=1024)
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserCreate(UserBase):
    password: str = Field(..., min_length=1, max_length=128)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=64)
    password: Optional[str] = Field(default=None, min_length=1, max_length=128)
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    profile_picture_url: Optional[str] = Field(default=None, max_length=1024)
    preferences: Optional[Dict[str, Any]] = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserResponse(BaseModel):
    id: int
    username: str
    role: Role
    is_active: bool
    profile_picture_url: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    items: List[UserResponse]
    limit: int
    offset: int


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
