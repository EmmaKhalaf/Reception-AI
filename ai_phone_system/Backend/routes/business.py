from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import time
from typing import List

from Backend.database import get_db
from Backend.models.business import Business, BusinessHours
from Backend.utils.auth import get_current_business_id  # we’ll add this next

router = APIRouter(prefix="/business", tags=["Business"])


# -----------------------------
# SCHEMAS (simple inline)
# -----------------------------
from pydantic import BaseModel


class HoursIn(BaseModel):
    day_of_week: int  # 0 = Monday, 6 = Sunday
    open_time: time
    close_time: time


# -----------------------------
# SET BUSINESS HOURS
# -----------------------------
@router.post("/hours")
def set_business_hours(
    hours: List[HoursIn],
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Clear existing hours
    db.query(BusinessHours).filter(
        BusinessHours.business_id == business_id
    ).delete()

    # Insert new hours
    for h in hours:
        db.add(
            BusinessHours(
                business_id=business_id,
                day_of_week=h.day_of_week,
                open_time=h.open_time,
                close_time=h.close_time,
            )
        )

    db.commit()
    return {"status": "ok", "message": "Business hours saved"}


# -----------------------------
# GET BUSINESS HOURS
# -----------------------------
@router.get("/hours")
def get_business_hours(
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    hours = db.query(BusinessHours).filter(
        BusinessHours.business_id == business_id
    ).all()

    return [
        {
            "day_of_week": h.day_of_week,
            "open_time": h.open_time,
            "close_time": h.close_time,
        }
        for h in hours
    ]