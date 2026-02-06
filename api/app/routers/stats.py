from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

from fastapi import APIRouter, Depends, Query

from ..db import get_connection
from ..security import require_role
from ..visibility import cache_role_key, visibility_clause_for_role

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)

CACHE_TTL = timedelta(minutes=2)

# Simple in-process cache because Railway runs a single worker by default.
_cache_lock = Lock()
_cache_payload: Dict[str, Dict[str, Any]] = {}
_cache_generated_at: Dict[str, datetime] = {}
_cache_expires_at: Dict[str, datetime] = {}

TableConfig = Dict[str, Any]

TABLES: List[TableConfig] = [
    {
        "key": "users",
        "table": "users",
        "alias": "u",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "visibility_column": False,
        "recent": {
            "fields": ["id", "username", "role", "created_at", "updated_at"],
            "order": "COALESCE(u.updated_at, u.created_at)",
            "limit": 5,
        },
    },
    {
        "key": "persons",
        "table": "persons",
        "alias": "p",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "visibility_column": True,
        "recent": {
            "fields": ["id", "first_name", "last_name", "status", "created_at", "updated_at"],
            "order": "COALESCE(p.updated_at, p.created_at)",
            "limit": 5,
        },
    },
    {
        "key": "notes",
        "table": "notes",
        "alias": "n",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "visibility_column": True,
        "joins": ["JOIN persons p ON p.id = n.person_id"],
        "visibility_aliases": ["n", "p"],
        "recent": {
            "fields": ["id", "person_id", "title", "created_at", "updated_at"],
            "order": "COALESCE(n.updated_at, n.created_at)",
            "limit": 5,
        },
    },
    {
        "key": "profiles",
        "table": "profiles",
        "alias": "pr",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "visibility_column": True,
        "recent": {
            "fields": ["id", "platform_id", "username", "status", "created_at", "updated_at"],
            "order": "COALESCE(pr.updated_at, pr.created_at)",
            "limit": 5,
        },
    },
    {
        "key": "activities",
        "table": "activities",
        "alias": "a",
        "created_field": "occurred_at",
        "updated_field": "updated_at",
        "visibility_column": True,
        "joins": ["JOIN persons p ON p.id = a.person_id"],
        "visibility_aliases": ["a", "p"],
        "recent": {
            "fields": ["id", "person_id", "activity_type", "occurred_at", "updated_at", "severity"],
            "order": "COALESCE(a.updated_at, a.occurred_at)",
            "limit": 5,
        },
    },
    {
        "key": "vehicles",
        "table": "vehicles",
        "alias": "v",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "visibility_column": True,
        "recent": None,
    },
    {
        "key": "platforms",
        "table": "platforms",
        "alias": "pf",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "visibility_column": True,
        "recent": None,
    },
]


def _max_timestamp(values: Iterable[Optional[datetime]]) -> Optional[datetime]:
    latest: Optional[datetime] = None
    for value in values:
        if value is None:
            continue
        if latest is None or value > latest:
            latest = value
    return latest


def _build_counts_sql(config: TableConfig, role: str) -> tuple[str, List[Any]]:
    select_parts = ["COUNT(*) AS total"]
    created_field = config.get("created_field")
    updated_field = config.get("updated_field")
    alias = config.get("alias", config["table"][0])
    if created_field:
        select_parts.append(f"MAX({alias}.{created_field}) AS last_created_at")
    else:
        select_parts.append("NULL AS last_created_at")
    if updated_field:
        select_parts.append(f"MAX({alias}.{updated_field}) AS last_updated_at")
    else:
        select_parts.append("NULL AS last_updated_at")
    sql = f"SELECT {', '.join(select_parts)} FROM {config['table']} {alias}"
    for join_clause in config.get("joins", []):
        sql += f" {join_clause}"
    params: List[Any] = []
    where_clauses: List[str] = []
    if config.get("visibility_column", True):
        visibility_aliases = config.get("visibility_aliases")
        if not visibility_aliases:
            visibility_aliases = [alias]
        for vis_alias in visibility_aliases:
            clause, clause_params = visibility_clause_for_role(role, alias=vis_alias)
            if clause:
                where_clauses.append(clause)
                params.extend(clause_params)
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    return f"{sql};", params


def _fetch_recent(cur, config: TableConfig, role: str) -> Optional[List[Dict[str, Any]]]:
    recent_config = config.get("recent")
    if not recent_config:
        return None
    alias = config.get("alias", config["table"][0])
    fields_list = []
    for field in recent_config["fields"]:
        if "." in field or "(" in field:
            fields_list.append(field)
        else:
            fields_list.append(f"{alias}.{field}")
    fields = ", ".join(fields_list)
    order = recent_config["order"]
    limit = recent_config.get("limit", 5)
    sql = f"SELECT {fields} FROM {config['table']} {alias}"
    for join_clause in config.get("joins", []):
        sql += f" {join_clause}"
    params: List[Any] = []
    if config.get("visibility_column", True):
        visibility_aliases = config.get("visibility_aliases")
        if not visibility_aliases:
            visibility_aliases = [alias]
        where_clauses: List[str] = []
        for vis_alias in visibility_aliases:
            clause, clause_params = visibility_clause_for_role(role, alias=vis_alias)
            if clause:
                where_clauses.append(clause)
                params.extend(clause_params)
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
    order_expr = order if "." in order or "(" in order else f"{alias}.{order}"
    sql += f" ORDER BY {order_expr} DESC NULLS LAST LIMIT %s;"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def _compute_stats(role: str) -> Dict[str, Any]:
    entities: Dict[str, Any] = {}
    recent: Dict[str, Any] = {}
    with get_connection() as conn, conn.cursor() as cur:
        for config in TABLES:
            counts_sql, count_params = _build_counts_sql(config, role)
            cur.execute(counts_sql, count_params)
            row = cur.fetchone()
            last_created = row.get("last_created_at")
            last_updated = row.get("last_updated_at")
            entities[config["key"]] = {
                "total": row.get("total", 0),
                "last_created_at": last_created,
                "last_updated_at": last_updated,
                "last_activity_at": _max_timestamp((last_created, last_updated)),
            }

            recent_rows = _fetch_recent(cur, config, role)
            if recent_rows is not None:
                recent[config["key"]] = recent_rows
    return {"entities": entities, "recent": recent}


def _make_response(payload: Dict[str, Any], generated_at: datetime, expires_at: datetime, cache_hit: bool) -> Dict[str, Any]:
    return {
        "meta": {
            "generated_at": generated_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_seconds": int(CACHE_TTL.total_seconds()),
            "cache_hit": cache_hit,
        },
        **payload,
    }


@router.get("/overview")
def stats_overview(
    force_refresh: bool = Query(False, description="Skip cached value and recompute instantly."),
    current_user: Dict = Depends(require_role("user", "admin")),
):
    global _cache_payload, _cache_generated_at, _cache_expires_at

    role_key = cache_role_key(current_user["role"])
    now = datetime.now(timezone.utc)
    with _cache_lock:
        payload = _cache_payload.get(role_key)
        generated_at = _cache_generated_at.get(role_key)
        expires_at = _cache_expires_at.get(role_key)
        if not force_refresh and payload and generated_at and expires_at and now < expires_at:
            return _make_response(payload, generated_at, expires_at, cache_hit=True)

    payload = _compute_stats(role_key)
    generated_at = datetime.now(timezone.utc)
    expires_at = generated_at + CACHE_TTL

    with _cache_lock:
        _cache_payload[role_key] = payload
        _cache_generated_at[role_key] = generated_at
        _cache_expires_at[role_key] = expires_at

    return _make_response(payload, generated_at, expires_at, cache_hit=False)
