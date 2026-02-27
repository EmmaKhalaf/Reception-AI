from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..utils.auth import get_current_business_id
from ..models.business import BusinessHours
from ..models.service import Service
from ..models.appointment import Appointment
from ..services.availability_service import get_available_slots

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("/")
def get_availability(
    date: str,
    service_id: str,
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    # Validate date format
    try:
        requested_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    day_of_week = requested_date.weekday()

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
        raise HTTPException(status_code=404, detail="Service not found")

    start_of_day = datetime.combine(requested_date.date(), datetime.min.time())
    end_of_day = datetime.combine(requested_date.date(), datetime.max.time())

    appointments = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.start_time >= start_of_day,
        Appointment.start_time <= end_of_day,
    ).all()

    slots = get_available_slots(
        business_hours=business_hours,
        appointments=appointments,
        service_duration_minutes=service.duration_minutes,
    )

    return {
        "date": date,
        "service_id": service_id,
        "available_slots": slots,
    }