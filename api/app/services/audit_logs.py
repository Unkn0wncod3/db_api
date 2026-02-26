from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import anyio
from fastapi import Request
from starlette.responses import Response

from ..db import get_connection

try:
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover
    Jsonb = dict  # type: ignore

AUDIT_COLUMNS = (
    "id, user_id, username, role, action, resource, resource_id, method, path, status_code,"
    " ip_address, user_agent, metadata, created_at"
)

logger = logging.getLogger(__name__)


def _write_log(payload: Dict[str, Any]) -> None:
    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    payload["metadata"] = Jsonb(metadata)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_logs (
                user_id, username, role, action, resource, resource_id,
                method, path, status_code, ip_address, user_agent, metadata
            )
            VALUES (
                %(user_id)s, %(username)s, %(role)s, %(action)s, %(resource)s, %(resource_id)s,
                %(method)s, %(path)s, %(status_code)s, %(ip_address)s, %(user_agent)s, %(metadata)s
            );
            """,
            payload,
        )
        conn.commit()


def log_event(
    *,
    user: Optional[Dict[str, Any]],
    action: str,
    resource: Optional[str],
    resource_id: Optional[int],
    method: str,
    path: str,
    status_code: int,
    ip_address: Optional[str],
    user_agent: Optional[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    payload = {
        "user_id": (user or {}).get("id"),
        "username": (user or {}).get("username"),
        "role": (user or {}).get("role"),
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "metadata": metadata or {},
    }
    try:
        _write_log(payload)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("audit log write failed: %s", exc)


async def log_request_event(
    request: Request,
    response: Response,
    *,
    status_code_override: Optional[int] = None,
) -> None:
    user = getattr(request.state, "current_user", None)
    route = request.scope.get("route")
    resource = getattr(route, "path", None) if route is not None else None
    action = f"{request.method} {resource or request.url.path}"
    path_params = getattr(request, "path_params", {}) or {}
    resource_id = _extract_resource_id(path_params)
    metadata: Dict[str, Any] = {}
    extra_metadata = getattr(request.state, "audit_metadata", None)
    if isinstance(extra_metadata, dict):
        metadata.update(extra_metadata)
    if request.url.query:
        metadata.setdefault("query_string", request.url.query)
    method = request.method
    path = request.url.path
    status_code = status_code_override or getattr(response, "status_code", 500)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await anyio.to_thread.run_sync(
        log_event,
        user=user,
        action=action,
        resource=resource,
        resource_id=resource_id,
        method=method,
        path=path,
        status_code=status_code,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata,
    )
    request.state.audit_metadata = None


def _extract_resource_id(path_params: Dict[str, Any]) -> Optional[int]:
    for key, value in path_params.items():
        if not isinstance(key, str):
            continue
        if not key.endswith("_id"):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            try:
                return int(value)
            except ValueError:
                continue
    return None


def list_logs(
    *,
    limit: int,
    offset: int,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
) -> Dict[str, Any]:
    clauses = []
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if user_id is not None:
        clauses.append("user_id = %(user_id)s")
        params["user_id"] = user_id
    if action:
        clauses.append("action ILIKE %(action)s")
        params["action"] = f"%{action}%"
    if resource:
        clauses.append("resource = %(resource)s")
        params["resource"] = resource
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"SELECT {AUDIT_COLUMNS} FROM audit_logs {where_clause} ORDER BY id DESC LIMIT %(limit)s OFFSET %(offset)s;"
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    for row in rows:
        if row.get("metadata") is None:
            row["metadata"] = {}
    return {"items": rows, "limit": limit, "offset": offset}
