from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter, Depends

from ..schemas import DashboardOverviewResponse
from ..security import get_optional_current_user
from ..services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
service = DashboardService()


@router.get("", response_model=DashboardOverviewResponse)
def get_dashboard(current_user: Optional[Dict] = Depends(get_optional_current_user)):
    return service.get_overview(current_user=current_user)
