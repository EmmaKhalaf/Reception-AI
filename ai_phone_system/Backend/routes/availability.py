from fastapi import APIRouter, Depends, HTTPException
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