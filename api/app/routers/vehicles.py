from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb

from ..db import get_connection
from ..schemas import VehicleCreate, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("")
def list_vehicles():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM vehicles ORDER BY id;")
        rows = cur.fetchall()
    return {"items": rows}


@router.post("", status_code=201)
def create_vehicle(payload: VehicleCreate):
    data = payload.model_dump()
    if data.get("metadata") is not None:
        data["metadata"] = Jsonb(data["metadata"])

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO vehicles (
                label, make, model, build_year, license_plate, vin, vehicle_type,
                energy_type, color, mileage_km, last_service_at, metadata
            ) VALUES (
                %(label)s,%(make)s,%(model)s,%(build_year)s,%(license_plate)s,%(vin)s,%(vehicle_type)s,
                %(energy_type)s,%(color)s,%(mileage_km)s,%(last_service_at)s,%(metadata)s
            ) RETURNING *;
            """,
            data,
        )
        row = cur.fetchone()
        conn.commit()
    return row


@router.patch("/{vehicle_id}")
def update_vehicle(vehicle_id: int, payload: VehicleUpdate):
    fields = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if not fields:
        raise HTTPException(400, "No fields to update")

    if fields.get("metadata") is not None:
        fields["metadata"] = Jsonb(fields["metadata"])

    set_sql = ", ".join([f"{column}=%({column})s" for column in fields])
    fields["vehicle_id"] = vehicle_id
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE vehicles SET {set_sql} WHERE id=%(vehicle_id)s RETURNING *;",
            fields,
        )
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Vehicle not found")
    return row


@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM vehicles WHERE id=%s RETURNING id;", (vehicle_id,))
        row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(404, "Vehicle not found")
    return {"deleted": row["id"]}
