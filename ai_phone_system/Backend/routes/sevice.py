from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..database import get_db
from ..models.service import Service
from ..utils.auth import get_current_business_id

router = APIRouter(prefix="/services", tags=["Services"])


class ServiceIn(BaseModel):
    name: str
    duration_minutes: int
    price_cents: int | None = None


class ServiceOut(BaseModel):
    id: str
    business_id: str
    name: str
    duration_minutes: int
    price_cents: int | None

    class Config:
        orm_mode = True


@router.post("/", response_model=ServiceOut, status_code=201)
def create_service(
    service: ServiceIn,
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    if service.duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="duration_minutes must be greater than 0")
    if service.price_cents is not None and service.price_cents < 0:
        raise HTTPException(status_code=400, detail="price_cents cannot be negative")

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


@router.get("/", response_model=List[ServiceOut])
def list_services(
    db: Session = Depends(get_db),
    business_id: str = Depends(get_current_business_id),
):
    return db.query(Service).filter(Service.business_id == business_id).all()