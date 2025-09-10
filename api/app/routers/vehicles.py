from fastapi import APIRouter
from ..db import get_connection
from ..schemas import VehicleCreate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.get("")
def list_vehicles():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM vehicles ORDER BY id;")
        rows = cur.fetchall()
    return {"items": rows}

@router.post("", status_code=201)
def create_vehicle(payload: VehicleCreate):
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
            payload.model_dump(),
        )
        row = cur.fetchone()
        conn.commit()
    return row
