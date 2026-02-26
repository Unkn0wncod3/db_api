from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException as FastAPIHTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from ..services import audit_logs

logger = logging.getLogger(__name__)


def register_audit_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def audit_logging(request: Request, call_next):
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
            except Exception as exc:  # pragma: no cover
                logger.warning("audit logging failed: %s", exc)
