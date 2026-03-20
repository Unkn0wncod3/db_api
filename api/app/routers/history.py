from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query

from ..core.enums import EntryChangeType
from ..schemas import GlobalHistoryListResponse
from ..security import get_optional_current_user
from ..services.entry_history import EntryHistoryService

router = APIRouter(prefix="/history", tags=["history"])
service = EntryHistoryService()


@router.get("", response_model=GlobalHistoryListResponse)
def list_global_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    schema_id: Optional[int] = Query(default=None),
    entry_id: Optional[int] = Query(default=None),
    changed_by: Optional[int] = Query(default=None),
    change_type: Optional[EntryChangeType] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    current_user: Optional[Dict] = Depends(get_optional_current_user),
):
    return service.list_global_history(
        current_user=current_user,
        limit=limit,
        offset=offset,
        search=search,
        schema_id=schema_id,
        entry_id=entry_id,
        changed_by=changed_by,
        change_type=change_type.value if change_type is not None else None,
        date_from=date_from,
        date_to=date_to,
    )
