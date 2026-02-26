from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.utils.auth import get_current_business_id
from app.models.business import BusinessHours
from app.models.service import Service
from app.models.appointment import Appointment
from app.services.availability_service import calculate_availability

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("/")
def get_availability(
    date: str,
    service_id: str,
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    day_of_week = datetime.strptime(date, "%Y-%m-%d").weekday()

    business_hours = db.query(BusinessHours).filter(
        BusinessHours.business_id == business_id,
        BusinessHours.day_of_week == day_of_week,
    ).first()

    if not business_hours:
        return {"available_slots": []}

    service = db.query(Service).filter(
        Service.id == service_id,
        Service.business_id == business_id,
    ).first()

    if not service:
        return {"available_slots": []}

    appointments = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.start_time >= f"{date} 00:00",
        Appointment.start_time <= f"{date} 23:59",
    ).all()

    slots = calculate_availability(
        business_hours=business_hours,
        appointments=appointments,
        service_duration_minutes=service.duration_minutes,
    )

    return {
        "date": date,
        "service_id": service_id,
        "available_slots": slots,
    }