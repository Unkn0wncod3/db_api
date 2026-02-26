from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query, Request

from ..roles import ADMIN_ROLES
from ..schemas import AuditLogListResponse
from ..security import require_role
from ..services import audit_logs as audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=AuditLogListResponse)
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: Optional[int] = Query(default=None, ge=1),
    action: Optional[str] = Query(default=None, max_length=128),
    resource: Optional[str] = Query(default=None, max_length=128),
    _: Dict = Depends(require_role(*ADMIN_ROLES)),
):
    return audit_service.list_logs(
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        resource=resource,
    )


@router.delete("/logs", status_code=204)
def delete_audit_logs(request: Request, _: Dict = Depends(require_role(*ADMIN_ROLES))):
    audit_service.clear_logs()
    audit_service.attach_request_metadata(
        request,
        event="audit_logs_cleared",
    )
