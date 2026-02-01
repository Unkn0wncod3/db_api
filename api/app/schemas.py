from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

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

# -------- Notes --------
class NoteCreate(BaseModel):
    title: Optional[str] = None
    text: str
    pinned: bool = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    pinned: Optional[bool] = None

# -------- Platforms --------
class PlatformCreate(BaseModel):
    name: str
    category: str = "social"
    base_url: Optional[str] = None
    api_base_url: Optional[str] = None
    is_active: bool = True

class PlatformUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    base_url: Optional[str] = None
    api_base_url: Optional[str] = None
    is_active: Optional[bool] = None

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

# -------- Person ↔ Profile --------
class LinkProfilePayload(BaseModel):
    profile_id: int
    note: Optional[str] = None

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

# -------- Activities --------
class ActivityCreate(BaseModel):
    person_id: int
    activity_type: str
    occurred_at: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    profile_id: Optional[int] = None
    community_id: Optional[int] = None
    item: Optional[str] = None
    notes: Optional[str] = None
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    severity: Optional[str] = None
    source: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geo_location: Optional[str] = None
    created_by: Optional[str] = None

class ActivityUpdate(BaseModel):
    person_id: Optional[int] = None
    activity_type: Optional[str] = None
    occurred_at: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    profile_id: Optional[int] = None
    community_id: Optional[int] = None
    item: Optional[str] = None
    notes: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    source: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geo_location: Optional[str] = None
    created_by: Optional[str] = None
