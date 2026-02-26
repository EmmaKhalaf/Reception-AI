from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.services.availability_service import get_available_slots

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("/")
def check_availability(
    business_id: str = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
    slot_minutes: int = 30,
    db: Session = Depends(get_db)
):
    """
    Returns available time slots for a business on a given date
    """

    date_obj = datetime.strptime(date, "%Y-%m-%d")

    slots = get_available_slots(
        db=db,
        business_id=business_id,
        date=date_obj,
        slot_minutes=slot_minutes
    )

    return {
        "business_id": business_id,
        "date": date,
        "available_slots": slots
    }