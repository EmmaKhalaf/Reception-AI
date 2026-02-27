from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.business_hours import BusinessHours
from pydantic import BaseModel
from datetime import time

router = APIRouter(prefix="/business_hours", tags=["business_hours"])

class BusinessHoursCreate(BaseModel):
    business_id: str
    day_of_week: int  # 0 = Monday, 6 = Sunday
    open_time: str    # "09:00"
    close_time: str   # "17:00"

@router.post("/create")
def create_business_hours(payload: BusinessHoursCreate, db: Session = Depends(get_db)):
    open_time_obj = time.fromisoformat(payload.open_time)
    close_time_obj = time.fromisoformat(payload.close_time)

    if close_time_obj <= open_time_obj:
        return {"error": "close_time must be after open_time"}

    bh = BusinessHours(
        business_id=payload.business_id,
        day_of_week=payload.day_of_week,
        open_time=open_time_obj,
        close_time=close_time_obj
    )

    db.add(bh)
    db.commit()
    db.refresh(bh)
    return {"success": True, "business_hours_id": bh.id}