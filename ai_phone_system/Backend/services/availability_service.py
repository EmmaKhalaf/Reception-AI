from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.business import BusinessHours
from app.models.appointment import Appointment

DEFAULT_SLOT_MINUTES = 30


def get_available_slots(
    db: Session,
    business_id: str,
    date: datetime,
    slot_minutes: int = DEFAULT_SLOT_MINUTES
):
    """
    Returns available time slots for a business on a given date
    """

    weekday = date.weekday()  # 0 = Monday

    # 1️⃣ Get business hours for that day
    hours = db.query(BusinessHours).filter(
        BusinessHours.business_id == business_id,
        BusinessHours.day_of_week == weekday
    ).first()

    if not hours:
        return []

    start_dt = datetime.combine(date.date(), hours.open_time)
    end_dt = datetime.combine(date.date(), hours.close_time)

    # 2️⃣ Get existing appointments for that day
    appointments = db.query(Appointment).filter(
        Appointment.business_id == business_id,
        Appointment.start_time >= start_dt,
        Appointment.start_time < end_dt
    ).all()

    booked_slots = [
        (appt.start_time, appt.end_time) for appt in appointments
    ]

    # 3️⃣ Generate slots
    slots = []
    current = start_dt

    while current + timedelta(minutes=slot_minutes) <= end_dt:
        slot_end = current + timedelta(minutes=slot_minutes)

        overlap = False
        for booked_start, booked_end in booked_slots:
            if not (slot_end <= booked_start or current >= booked_end):
                overlap = True
                break

        if not overlap:
            slots.append(current.strftime("%H:%M"))

        current += timedelta(minutes=slot_minutes)

    return slots