from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models.appointment import Appointment
from app.models.business import Business

router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ---------------------------------------------------------
# CREATE APPOINTMENT (BOOK)
# ---------------------------------------------------------
@router.post("/book")
def book_appointment(
    business_id: str,
    customer_name: str,
    customer_phone: str,
    start_time: datetime,
    duration_minutes: int = 30,
    db: Session = Depends(get_db),
):
    # 1️⃣ Validate business
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    end_time = start_time + timedelta(minutes=duration_minutes)

    # 2️⃣ Check conflicts
    conflict = (
        db.query(Appointment)
        .filter(
            Appointment.business_id == business_id,
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
            Appointment.status == "scheduled",
        )
        .first()
    )

    if conflict:
        raise HTTPException(status_code=409, detail="Time slot not available")

    # 3️⃣ Create appointment
    appointment = Appointment(
        business_id=business_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        start_time=start_time,
        end_time=end_time,
        status="scheduled",
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return {
        "status": "booked",
        "appointment_id": appointment.id,
        "start_time": appointment.start_time,
        "end_time": appointment.end_time,
    }


# ---------------------------------------------------------
# LIST APPOINTMENTS FOR A BUSINESS
# ---------------------------------------------------------
@router.get("/")
def list_appointments(
    business_id: str,
    db: Session = Depends(get_db),
):
    appointments = (
        db.query(Appointment)
        .filter(Appointment.business_id == business_id)
        .order_by(Appointment.start_time)
        .all()
    )

    return appointments


# ---------------------------------------------------------
# CANCEL APPOINTMENT
# ---------------------------------------------------------
@router.post("/cancel")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = "cancelled"
    db.commit()

    return {"status": "cancelled"}