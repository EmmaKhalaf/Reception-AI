from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()

# TEMP in-memory store (DB later)
appointments = []

@router.post("/")
def create_appointment(
    business_id: str,
    customer_name: str,
    start_time: datetime,
    end_time: datetime,
):
    appointment = {
        "business_id": business_id,
        "customer_name": customer_name,
        "start_time": start_time,
        "end_time": end_time,
    }

    appointments.append(appointment)
    return {"status": "booked", "appointment": appointment}


@router.get("/")
def list_appointments(business_id: str):
    return [
        a for a in appointments
        if a["business_id"] == business_id
    ]