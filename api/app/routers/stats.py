from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

from fastapi import APIRouter, Query

from ..db import get_connection

router = APIRouter(prefix="/stats", tags=["stats"])

CACHE_TTL = timedelta(minutes=2)

# Simple in-process cache because Railway runs a single worker by default.
_cache_lock = Lock()
_cache_payload: Optional[Dict[str, Any]] = None
_cache_generated_at: Optional[datetime] = None
_cache_expires_at: Optional[datetime] = None

TableConfig = Dict[str, Any]

TABLES: List[TableConfig] = [
    {
        "key": "persons",
        "table": "persons",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "recent": {
            "fields": ["id", "first_name", "last_name", "status", "created_at", "updated_at"],
            "order": "COALESCE(updated_at, created_at)",
            "limit": 5,
        },
    },
    {
        "key": "notes",
        "table": "notes",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "recent": {
            "fields": ["id", "person_id", "title", "created_at", "updated_at"],
            "order": "COALESCE(updated_at, created_at)",
            "limit": 5,
        },
    },
    {
        "key": "profiles",
        "table": "profiles",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "recent": {
            "fields": ["id", "platform_id", "username", "status", "created_at", "updated_at"],
            "order": "COALESCE(updated_at, created_at)",
            "limit": 5,
        },
    },
    {
        "key": "activities",
        "table": "activities",
        "created_field": "occurred_at",
        "updated_field": "updated_at",
        "recent": {
            "fields": ["id", "person_id", "activity_type", "occurred_at", "updated_at", "severity"],
            "order": "COALESCE(updated_at, occurred_at)",
            "limit": 5,
        },
    },
    {
        "key": "vehicles",
        "table": "vehicles",
        "created_field": "created_at",
        "updated_field": "updated_at",
        "recent": None,
    },
    {
        "key": "platforms",
        "table": "platforms",
        "created_field": "created_at",
        "updated_field": "updated_at",
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


def _build_counts_sql(config: TableConfig) -> str:
    select_parts = ["COUNT(*) AS total"]
    created_field = config.get("created_field")
    updated_field = config.get("updated_field")
    if created_field:
        select_parts.append(f"MAX({created_field}) AS last_created_at")
    else:
        select_parts.append("NULL AS last_created_at")
    if updated_field:
        select_parts.append(f"MAX({updated_field}) AS last_updated_at")
    else:
        select_parts.append("NULL AS last_updated_at")
    return f"SELECT {', '.join(select_parts)} FROM {config['table']};"


def _fetch_recent(cur, config: TableConfig) -> Optional[List[Dict[str, Any]]]:
    recent_config = config.get("recent")
    if not recent_config:
        return None
    fields = ", ".join(recent_config["fields"])
    order = recent_config["order"]
    limit = recent_config.get("limit", 5)
    sql = f"SELECT {fields} FROM {config['table']} ORDER BY {order} DESC NULLS LAST LIMIT %s;"
    cur.execute(sql, (limit,))
    return cur.fetchall()


def _compute_stats() -> Dict[str, Any]:
    entities: Dict[str, Any] = {}
    recent: Dict[str, Any] = {}
    with get_connection() as conn, conn.cursor() as cur:
        for config in TABLES:
            counts_sql = _build_counts_sql(config)
            cur.execute(counts_sql)
            row = cur.fetchone()
            last_created = row.get("last_created_at")
            last_updated = row.get("last_updated_at")
            entities[config["key"]] = {
                "total": row.get("total", 0),
                "last_created_at": last_created,
                "last_updated_at": last_updated,
                "last_activity_at": _max_timestamp((last_created, last_updated)),
            }

            recent_rows = _fetch_recent(cur, config)
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
def stats_overview(force_refresh: bool = Query(False, description="Skip cached value and recompute instantly.")):
    global _cache_payload, _cache_generated_at, _cache_expires_at

    now = datetime.now(timezone.utc)
    with _cache_lock:
        if (
            not force_refresh
            and _cache_payload is not None
            and _cache_generated_at is not None
            and _cache_expires_at is not None
            and now < _cache_expires_at
        ):
            return _make_response(_cache_payload, _cache_generated_at, _cache_expires_at, cache_hit=True)

    payload = _compute_stats()
    generated_at = datetime.now(timezone.utc)
    expires_at = generated_at + CACHE_TTL

    with _cache_lock:
        _cache_payload = payload
        _cache_generated_at = generated_at
        _cache_expires_at = expires_at

    return _make_response(payload, generated_at, expires_at, cache_hit=False)
