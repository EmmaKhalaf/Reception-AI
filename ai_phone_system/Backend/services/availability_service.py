from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from Backend.models.business import BusinessHours
from Backend.models.appointment import Appointment

DEFAULT_SLOT_MINUTES = 30
SLOT_INCREMENT_MINUTES = 15  # step between possible slots
BUFFER_MINUTES = 5  # optional buffer after appointments


def get_available_slots(
        db: Session,
        business_id: str,
        date: datetime,
        service_duration_minutes: int,
        slot_increment_minutes: int = SLOT_INCREMENT_MINUTES,
        buffer_minutes: int = BUFFER_MINUTES
):
    """
    Returns available time slots for a business on a given date.

    Slots are generated in increments of `slot_increment_minutes`.
    Appointments are respected with an optional `buffer_minutes` between them.
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
        Appointment.start_time < end_dt,  # appointments that overlap the day
        Appointment.end_time > start_dt
    ).all()

    booked_slots = [
        (appt.start_time - timedelta(minutes=buffer_minutes),
         appt.end_time + timedelta(minutes=buffer_minutes))
        for appt in appointments
    ]
    booked_slots.sort()  # optional, for faster checking

    # 3️⃣ Generate available slots
    slots = []
    current = start_dt

    while current + timedelta(minutes=service_duration_minutes) <= end_dt:
        slot_end = current + timedelta(minutes=service_duration_minutes)

        # Check for overlaps
        overlap = any(not (slot_end <= bs or current >= be) for bs, be in booked_slots)
        if not overlap:
            slots.append((current.strftime("%H:%M"), slot_end.strftime("%H:%M")))

        current += timedelta(minutes=slot_increment_minutes)

    return slots