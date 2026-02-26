from typing import Optional, Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..roles import ADMIN_ROLES, EDITOR_ROLES, READ_ROLES
from ..schemas import PersonCreate, PersonDossierResponse, PersonUpdate
from ..security import require_role
from ..services import audit_logs, dossiers as dossier_service
from ..visibility import visibility_clause_for_role

DEPENDENT_TABLES = ("notes", "person_profile_map", "activities")


router = APIRouter(
    prefix="/persons",
    tags=["persons"],
)


def _propagate_person_visibility(cur, person_id: int, visibility_level: str) -> None:
    for table in DEPENDENT_TABLES:
        cur.execute(
            f"UPDATE {table} SET visibility_level=%s WHERE person_id=%s;",
            (visibility_level, person_id),
        )


@router.get("")
def list_persons(
    q: Optional[str] = Query(default=None, description="Suche in first_name/last_name/email"),
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(require_role(*READ_ROLES)),
):
    sql = """
    SELECT p.id, p.first_name, p.last_name, p.email, p.status, p.tags, p.created_at, p.updated_at, p.visibility_level
    FROM persons p
    WHERE 1=1
    """
    params: List[Any] = []
    if q:
        sql += " AND (first_name ILIKE %s OR last_name ILIKE %s OR email ILIKE %s)"
        like = f"%{q}%"
        params += [like, like, like]
    if tag:
        sql += " AND %s = ANY(tags)"
        params.append(tag)
    clause, clause_params = visibility_clause_for_role(current_user["role"], alias="p")
    if clause:
        sql += f" AND {clause}"
        params.extend(clause_params)
    sql += " ORDER BY id LIMIT %s OFFSET %s"
    params += [limit, offset]
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/{person_id}")
def get_person(person_id: int, current_user: Dict[str, Any] = Depends(require_role(*READ_ROLES))):
    with get_connection() as conn, conn.cursor() as cur:
        sql = "SELECT * FROM persons p WHERE p.id=%s"
        params: List[Any] = [person_id]
        clause, clause_params = visibility_clause_for_role(current_user["role"], alias="p")
        if clause:
            sql += f" AND {clause}"
            params.extend(clause_params)
        cur.execute(sql, params)
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Person not found")
    return row


@router.post("", status_code=201, dependencies=[Depends(require_role(*EDITOR_ROLES))])
def create_person(payload: PersonCreate, request: Request):
    with get_connection() as conn, conn.cursor() as cur:
        data = payload.model_dump()
        if data.get("metadata") is not None:
            data["metadata"] = Jsonb(data["metadata"])

        cur.execute(
            """
            INSERT INTO persons (
                first_name,last_name,date_of_birth,gender,email,phone_number,
                address_line1,address_line2,postal_code,city,region_state,country,
                status,nationality,occupation,risk_level,tags,notes,metadata,visibility_level
            ) VALUES (
                %(first_name)s,%(last_name)s,%(date_of_birth)s,%(gender)s,%(email)s,%(phone_number)s,
                %(address_line1)s,%(address_line2)s,%(postal_code)s,%(city)s,%(region_state)s,%(country)s,
                %(status)s,%(nationality)s,%(occupation)s,%(risk_level)s,%(tags)s,%(notes)s,%(metadata)s,%(visibility_level)s
            ) RETURNING *;
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
    audit_logs.attach_request_metadata(
        request,
        event="person_created",
        person_id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        visibility=row["visibility_level"],
    )
    return row


@router.patch("/{person_id}", dependencies=[Depends(require_role(*EDITOR_ROLES))])
def update_person(person_id: int, payload: PersonUpdate, request: Request):
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(400, "No fields to update")

    if fields.get("metadata") is not None:
        fields["metadata"] = Jsonb(fields["metadata"])

    set_sql = ", ".join([f"{k}=%({k})s" for k in fields.keys()])
    fields["person_id"] = person_id
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"UPDATE persons SET {set_sql} WHERE id=%(person_id)s RETURNING *;", fields)
        row = cur.fetchone()
        if "visibility_level" in fields:
            _propagate_person_visibility(cur, person_id, fields["visibility_level"])
        conn.commit()
    if not row:
        raise HTTPException(404, "Person not found")
    audit_logs.attach_request_metadata(
        request,
        event="person_updated",
        person_id=row["id"],
        changed_fields=sorted(fields.keys()),
    )
    return row


@router.delete("/{person_id}", dependencies=[Depends(require_role(*ADMIN_ROLES))])
def delete_person(person_id: int, request: Request):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM persons WHERE id=%s RETURNING id, first_name, last_name;", (person_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Person not found")
    audit_logs.attach_request_metadata(
        request,
        event="person_deleted",
        person_id=row["id"],
        first_name=row.get("first_name"),
        last_name=row.get("last_name"),
    )
    return {"deleted": row["id"]}


@router.get("/{person_id}/dossier", response_model=PersonDossierResponse)
def get_person_dossier(
    person_id: int,
    request: Request,
    response: Response,
    current_user: Dict[str, Any] = Depends(require_role(*READ_ROLES)),
    profiles_limit: int = Query(5, ge=0, le=50),
    notes_limit: int = Query(5, ge=0, le=50),
    activities_limit: int = Query(5, ge=0, le=50),
):
    dossier, etag = dossier_service.fetch_person_dossier(
        person_id,
        current_user=current_user,
        profile_limit=profiles_limit,
        note_limit=notes_limit,
        activity_limit=activities_limit,
    )
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)
    response.headers["ETag"] = etag
    return dossier


@router.get("/{person_id}/dossier.pdf")
def get_person_dossier_pdf(
    person_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_role(*READ_ROLES)),
    profiles_limit: int = Query(5, ge=0, le=50),
    notes_limit: int = Query(5, ge=0, le=50),
    activities_limit: int = Query(5, ge=0, le=50),
):
    dossier, etag = dossier_service.fetch_person_dossier(
        person_id,
        current_user=current_user,
        profile_limit=profiles_limit,
        note_limit=notes_limit,
        activity_limit=activities_limit,
    )
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)
    pdf_bytes = dossier_service.render_dossier_pdf(dossier)
    pdf_response = Response(content=pdf_bytes, media_type="application/pdf")
    pdf_response.headers["Content-Disposition"] = f'attachment; filename="person_{person_id}_dossier.pdf"'
    pdf_response.headers["ETag"] = etag
    return pdf_response
