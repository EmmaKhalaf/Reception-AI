from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models.service import Service
from app.utils.auth import get_current_business_id

router = APIRouter(prefix="/services", tags=["Services"])


class ServiceIn(BaseModel):
    name: str
    duration_minutes: int
    price_cents: int | None = None


@router.post("/")
def create_service(
    service: ServiceIn,
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    s = Service(
        business_id=business_id,
        name=service.name,
        duration_minutes=service.duration_minutes,
        price_cents=service.price_cents,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/")
def list_services(
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    return db.query(Service).filter(Service.business_id == business_id).all()