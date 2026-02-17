from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from .visibility import VisibilityLevel, VISIBILITY_USER

# -------- Persons --------
class PersonCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    date_of_birth: Optional[date] = None
    gender: str = "Unspecified"
    email: str = "not_provided@example.com"
    phone_number: str = "N/A"
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    region_state: Optional[str] = None
    country: Optional[str] = None
    status: str = "active"
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    risk_level: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    visibility_level: VisibilityLevel = VISIBILITY_USER

class PersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    region_state: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None
    archived_at: Optional[datetime] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    risk_level: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    visibility_level: Optional[VisibilityLevel] = None

# -------- Notes --------
class NoteCreate(BaseModel):
    title: Optional[str] = None
    text: str
    pinned: bool = False
    visibility_level: VisibilityLevel = VISIBILITY_USER

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    pinned: Optional[bool] = None
    visibility_level: Optional[VisibilityLevel] = None

# -------- Platforms --------
class PlatformCreate(BaseModel):
    name: str
    category: str = "social"
    base_url: Optional[str] = None
    api_base_url: Optional[str] = None
    is_active: bool = True
    visibility_level: VisibilityLevel = VISIBILITY_USER

class PlatformUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    base_url: Optional[str] = None
    api_base_url: Optional[str] = None
    is_active: Optional[bool] = None
    visibility_level: Optional[VisibilityLevel] = None

# -------- Profiles --------
class ProfileCreate(BaseModel):
    platform_id: int
    username: str
    external_id: Optional[str] = None
    display_name: Optional[str] = None
    url: Optional[str] = None
    status: str = "active"
    last_seen_at: Optional[datetime] = None
    language: Optional[str] = None
    region: Optional[str] = None
    is_verified: bool = False
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    visibility_level: VisibilityLevel = VISIBILITY_USER

class ProfileUpdate(BaseModel):
    platform_id: Optional[int] = None
    username: Optional[str] = None
    external_id: Optional[str] = None
    display_name: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    language: Optional[str] = None
    region: Optional[str] = None
    is_verified: Optional[bool] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    visibility_level: Optional[VisibilityLevel] = None

# -------- Person ↔ Profile --------
class LinkProfilePayload(BaseModel):
    profile_id: int
    note: Optional[str] = None
    visibility_level: Optional[VisibilityLevel] = None

# -------- Vehicles --------
class VehicleCreate(BaseModel):
    label: str
    make: Optional[str] = None
    model: Optional[str] = None
    build_year: Optional[int] = None
    license_plate: Optional[str] = None
    vin: Optional[str] = None
    vehicle_type: Optional[str] = None
    energy_type: Optional[str] = None
    color: Optional[str] = None
    mileage_km: Optional[int] = None
    last_service_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    visibility_level: VisibilityLevel = VISIBILITY_USER

class VehicleUpdate(BaseModel):
    label: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    build_year: Optional[int] = None
    license_plate: Optional[str] = None
    vin: Optional[str] = None
    vehicle_type: Optional[str] = None
    energy_type: Optional[str] = None
    color: Optional[str] = None
    mileage_km: Optional[int] = None
    last_service_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    visibility_level: Optional[VisibilityLevel] = None

# -------- Activities --------
class ActivityCreate(BaseModel):
    person_id: int
    activity_type: str
    occurred_at: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    profile_id: Optional[int] = None
    item: Optional[str] = None
    notes: Optional[str] = None
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    severity: Optional[str] = None
    source: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geo_location: Optional[str] = None
    created_by: Optional[str] = None
    visibility_level: VisibilityLevel = VISIBILITY_USER

class ActivityUpdate(BaseModel):
    person_id: Optional[int] = None
    activity_type: Optional[str] = None
    occurred_at: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    profile_id: Optional[int] = None
    item: Optional[str] = None
    notes: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    source: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geo_location: Optional[str] = None
    created_by: Optional[str] = None
    visibility_level: Optional[VisibilityLevel] = None

# -------- Users & Auth --------
Role = Literal["admin", "user"]


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    role: Role = "user"
    profile_picture_url: Optional[str] = Field(default=None, max_length=1024)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=64)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    profile_picture_url: Optional[str] = Field(default=None, max_length=1024)
    preferences: Optional[Dict[str, Any]] = None


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
