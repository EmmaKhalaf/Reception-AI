from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.business import BusinessHours
from pydantic import BaseModel
from datetime import time

router = APIRouter(prefix="/business_hours", tags=["business_hours"])

class BusinessHoursCreate(BaseModel):
    business_id: str
    day_of_week: int  # 0 = Monday, 6 = Sunday
    open_time: str    # "09:00"
    close_time: str   # "17:00"

@router.post("/create", status_code=201)
def create_business_hours(payload: BusinessHoursCreate, db: Session = Depends(get_db)):
    # Validate day_of_week
    if not 0 <= payload.day_of_week <= 6:
        raise HTTPException(status_code=400, detail="day_of_week must be between 0 (Monday) and 6 (Sunday)")

    # Validate time format
    try:
        open_time_obj = time.fromisoformat(payload.open_time)
        close_time_obj = time.fromisoformat(payload.close_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Time must be in HH:MM format")

    if close_time_obj <= open_time_obj:
        raise HTTPException(status_code=400, detail="close_time must be after open_time")

    bh = BusinessHours(
        business_id=payload.business_id,
        day_of_week=payload.day_of_week,
        open_time=open_time_obj,
        close_time=close_time_obj
    )

    db.add(bh)
    db.commit()
    db.refresh(bh)

    return {"success": True, "business_hours": {
        "id": bh.id,
        "business_id": bh.business_id,
        "day_of_week": bh.day_of_week,
        "open_time": bh.open_time.isoformat(),
        "close_time": bh.close_time.isoformat()
    }}