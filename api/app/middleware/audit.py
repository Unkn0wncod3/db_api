from __future__ import annotations

from fastapi import HTTPException as FastAPIHTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..services import audit_logs


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not hasattr(request.state, "current_user"):
            request.state.current_user = None

        response: Response | None = None
        status_override = None
        try:
            response = await call_next(request)
            return response
        except (FastAPIHTTPException, StarletteHTTPException) as exc:
            status_override = exc.status_code
            raise
        except Exception:
            status_override = 500
            raise
        finally:
            resp = response or Response(status_code=status_override or 500)
            try:
                await audit_logs.log_request_event(
                    request,
                    resp,
                    status_code_override=status_override,
                )
            except Exception:
                # Never block requests due to logging issues
                pass
