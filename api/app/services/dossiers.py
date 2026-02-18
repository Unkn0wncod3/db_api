import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, status

from ..db import get_connection
from ..visibility import allowed_visibility_levels, is_admin_role, visibility_clause_for_role

DEFAULT_LIMIT = 5


def _normalize_tags(value):
    if value is None:
        return []
    return value


def _normalize_metadata(value):
    if value is None:
        return {}
    return value


def _fetch_person(cur, person_id: int, role: str) -> Dict[str, Any]:
    sql = """
    SELECT
        p.id, p.first_name, p.last_name, p.date_of_birth, p.gender, p.email,
        p.phone_number, p.city, p.region_state, p.country, p.status, p.risk_level,
        p.tags, p.metadata, p.visibility_level, p.created_at, p.updated_at,
        p.archived_at, p.nationality, p.occupation
    FROM persons p
    WHERE p.id=%s
    """
    params: List[Any] = [person_id]
    clause, clause_params = visibility_clause_for_role(role, alias="p")
    if clause:
        sql += f" AND {clause}"
        params.extend(clause_params)
    cur.execute(sql, params)
    row = cur.fetchone()
    if not row:
        return {}
    row["tags"] = _normalize_tags(row.get("tags"))
    row["metadata"] = _normalize_metadata(row.get("metadata"))
    return row


def _apply_visibility(sql: str, params: List[Any], role: str, alias: str) -> Tuple[str, List[Any]]:
    clause, clause_params = visibility_clause_for_role(role, alias=alias)
    if clause:
        sql += f" AND {clause}"
        params.extend(clause_params)
    return sql, params


def _fetch_profiles(cur, person_id: int, role: str, limit: int) -> List[Dict[str, Any]]:
    if limit == 0:
        return []
    sql = """
    SELECT
        pr.id,
        pr.platform_id,
        pf.name AS platform_name,
        pr.username,
        pr.display_name,
        pr.status,
        pr.visibility_level,
        pr.last_seen_at,
        pr.created_at,
        pr.updated_at,
        ppm.visibility_level AS link_visibility_level,
        ppm.linked_at
    FROM person_profile_map ppm
    JOIN profiles pr ON pr.id = ppm.profile_id
    LEFT JOIN platforms pf ON pf.id = pr.platform_id
    WHERE ppm.person_id=%s
    """
    params: List[Any] = [person_id]
    sql, params = _apply_visibility(sql, params, role, alias="ppm")
    sql, params = _apply_visibility(sql, params, role, alias="pr")
    sql += " ORDER BY COALESCE(pr.updated_at, pr.created_at) DESC NULLS LAST LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def _fetch_notes(cur, person_id: int, role: str, limit: int) -> List[Dict[str, Any]]:
    if limit == 0:
        return []
    sql = """
    SELECT
        n.id,
        n.title,
        n.text,
        n.pinned,
        n.visibility_level,
        n.created_at,
        n.updated_at
    FROM notes n
    JOIN persons p ON p.id = n.person_id
    WHERE n.person_id=%s
    """
    params: List[Any] = [person_id]
    sql, params = _apply_visibility(sql, params, role, alias="n")
    sql, params = _apply_visibility(sql, params, role, alias="p")
    sql += " ORDER BY COALESCE(n.updated_at, n.created_at) DESC LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def _fetch_activities(cur, person_id: int, role: str, limit: int) -> List[Dict[str, Any]]:
    if limit == 0:
        return []
    sql = """
    SELECT
        a.id,
        a.activity_type,
        a.occurred_at,
        a.notes,
        a.severity,
        a.source,
        a.visibility_level,
        a.created_by,
        a.updated_at,
        a.person_id
    FROM activities a
    JOIN persons p ON p.id = a.person_id
    WHERE a.person_id=%s
    """
    params: List[Any] = [person_id]
    sql, params = _apply_visibility(sql, params, role, alias="a")
    sql, params = _apply_visibility(sql, params, role, alias="p")
    sql += " ORDER BY COALESCE(a.updated_at, a.occurred_at) DESC LIMIT %s"
    params.append(limit)
    cur.execute(sql, params)
    return cur.fetchall()


def _fetch_stats(cur, person_id: int, role: str) -> Dict[str, Any]:
    stats: Dict[str, Any] = {}

    def run(query: str, params: List[Any]) -> Dict[str, Any]:
        cur.execute(query, params)
        row = cur.fetchone()
        return row or {"total": 0, "last_updated_at": None}

    profile_sql = """
        SELECT
            COUNT(*) AS total,
            MAX(COALESCE(pr.updated_at, pr.created_at)) AS last_updated_at
        FROM person_profile_map ppm
        JOIN profiles pr ON pr.id = ppm.profile_id
        WHERE ppm.person_id=%s
    """
    profile_params: List[Any] = [person_id]
    profile_sql, profile_params = _apply_visibility(profile_sql, profile_params, role, alias="ppm")
    profile_sql, profile_params = _apply_visibility(profile_sql, profile_params, role, alias="pr")
    stats["profiles"] = run(profile_sql, profile_params)

    notes_sql = """
        SELECT
            COUNT(*) AS total,
            MAX(COALESCE(n.updated_at, n.created_at)) AS last_updated_at
        FROM notes n
        JOIN persons p ON p.id = n.person_id
        WHERE n.person_id=%s
    """
    notes_params: List[Any] = [person_id]
    notes_sql, notes_params = _apply_visibility(notes_sql, notes_params, role, alias="n")
    notes_sql, notes_params = _apply_visibility(notes_sql, notes_params, role, alias="p")
    stats["notes"] = run(notes_sql, notes_params)

    activities_sql = """
        SELECT
            COUNT(*) AS total,
            MAX(COALESCE(a.updated_at, a.occurred_at)) AS last_updated_at
        FROM activities a
        JOIN persons p ON p.id = a.person_id
        WHERE a.person_id=%s
    """
    activities_params: List[Any] = [person_id]
    activities_sql, activities_params = _apply_visibility(activities_sql, activities_params, role, alias="a")
    activities_sql, activities_params = _apply_visibility(activities_sql, activities_params, role, alias="p")
    stats["activities"] = run(activities_sql, activities_params)

    return stats


def _build_person_payload(row: Dict[str, Any], role: str) -> Dict[str, Any]:
    allowed_levels = list(allowed_visibility_levels(role))
    person_payload = {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "date_of_birth": row.get("date_of_birth"),
        "gender": row.get("gender"),
        "email": row.get("email"),
        "phone_number": row.get("phone_number"),
        "city": row.get("city"),
        "region_state": row.get("region_state"),
        "country": row.get("country"),
        "status": row.get("status"),
        "risk_level": row.get("risk_level"),
        "tags": row.get("tags"),
        "metadata": row.get("metadata"),
        "visibility_level": row.get("visibility_level"),
        "visibility_scope": allowed_levels,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "archived_at": row.get("archived_at"),
        "nationality": row.get("nationality"),
        "occupation": row.get("occupation"),
    }
    return person_payload


def _build_audit(person: Dict[str, Any], latest_activity: Dict[str, Any]) -> Dict[str, Any]:
    audit = {
        "created_at": person.get("created_at"),
        "updated_at": person.get("updated_at"),
        "created_by": person.get("created_by"),
        "last_activity": None,
    }
    if latest_activity:
        audit["last_activity"] = {
            "id": latest_activity.get("id"),
            "activity_type": latest_activity.get("activity_type"),
            "occurred_at": latest_activity.get("occurred_at"),
            "visibility_level": latest_activity.get("visibility_level"),
            "notes": latest_activity.get("notes"),
            "severity": latest_activity.get("severity"),
        }
    return audit


def _serialize_for_etag(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, default=_json_default, sort_keys=True)


def _json_default(value):
    if isinstance(value, (datetime,)):
        return value.isoformat()
    return value


def _compute_etag(person: Dict[str, Any], stats: Dict[str, Any]) -> str:
    base = {
        "person_id": person["id"],
        "person_updated": person.get("updated_at") or person.get("created_at"),
        "stats": stats,
    }
    serialized = _serialize_for_etag(base)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def fetch_person_dossier(
    person_id: int,
    *,
    current_user: Dict[str, Any],
    profile_limit: int = DEFAULT_LIMIT,
    note_limit: int = DEFAULT_LIMIT,
    activity_limit: int = DEFAULT_LIMIT,
) -> Tuple[Dict[str, Any], str]:
    role = current_user.get("role")
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing role for dossier request")

    with get_connection() as conn, conn.cursor() as cur:
        person = _fetch_person(cur, person_id, role)
        if not person:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

        profiles = _fetch_profiles(cur, person_id, role, profile_limit)
        notes = _fetch_notes(cur, person_id, role, note_limit)
        activities = _fetch_activities(cur, person_id, role, activity_limit)
        stats = _fetch_stats(cur, person_id, role)

    latest_activity = activities[0] if activities else None
    dossier = {
        "person": _build_person_payload(person, role),
        "relations": {
            "profiles": profiles,
            "notes": notes,
            "activities": activities,
        },
        "stats": stats,
        "audit": _build_audit(person, latest_activity),
        "meta": {
            "can_view_admin_sections": is_admin_role(role),
            "limits": {
                "profiles": profile_limit,
                "notes": note_limit,
                "activities": activity_limit,
            },
        },
    }
    etag = _compute_etag(person, stats)
    return dossier, etag


def render_dossier_pdf(dossier: Dict[str, Any], brand_label: str = "DB API") -> bytes:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise RuntimeError("fpdf2 is required for dossier PDF generation. Install via requirements.") from exc

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"{brand_label} - Person Dossier", ln=True)

    person = dossier["person"]
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"{person['first_name']} {person['last_name']} (#{person['id']})", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, f"Status: {person.get('status') or 'n/a'} | Risk: {person.get('risk_level') or 'n/a'}")
    pdf.multi_cell(0, 6, f"Email: {person.get('email') or 'n/a'}")
    pdf.multi_cell(0, 6, f"Location: {person.get('city') or ''} {person.get('region_state') or ''} {person.get('country') or ''}".strip())
    pdf.ln(4)

    def section(title: str):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("Helvetica", "", 11)

    section("Profiles")
    profiles = dossier["relations"]["profiles"]
    if not profiles:
        pdf.cell(0, 6, "No profiles within visibility scope.", ln=True)
    else:
        for profile in profiles:
            pdf.multi_cell(
                0,
                6,
                f"- {profile.get('platform_name') or 'Platform'} / {profile.get('username')} "
                f"(status: {profile.get('status')})",
            )
    pdf.ln(2)

    section("Notes")
    notes = dossier["relations"]["notes"]
    if not notes:
        pdf.cell(0, 6, "No notes within visibility scope.", ln=True)
    else:
        for note in notes:
            title = note.get("title") or "Untitled"
            pdf.multi_cell(0, 6, f"- {title}: {note.get('text')[:140]}".strip())
    pdf.ln(2)

    section("Recent Activities")
    activities = dossier["relations"]["activities"]
    if not activities:
        pdf.cell(0, 6, "No activities within visibility scope.", ln=True)
    else:
        for activity in activities:
            occurred = activity.get("occurred_at")
            occurred_str = occurred.isoformat() if isinstance(occurred, datetime) else str(occurred)
            pdf.multi_cell(
                0,
                6,
                f"- {occurred_str}: {activity.get('activity_type')} ({activity.get('severity') or 'n/a'})",
            )

    pdf.ln(4)
    section("Stats")
    stats = dossier["stats"]
    pdf.multi_cell(
        0,
        6,
        f"Profiles: {stats['profiles']['total']} | Notes: {stats['notes']['total']} | Activities: {stats['activities']['total']}",
    )

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return pdf_bytes
