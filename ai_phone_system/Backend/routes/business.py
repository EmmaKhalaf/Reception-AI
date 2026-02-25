from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.business import Business

router = APIRouter()


# ---- DB dependency (local for now, we’ll centralize later) ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---- Create a business ----
@router.post("/")
def create_business(
    name: str,
    phone_number: str | None = None,
    timezone: str = "UTC",
    db: Session = Depends(get_db)
):
    business = Business(
        name=name,
        phone_number=phone_number,
        timezone=timezone,
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    return {
        "id": business.id,
        "name": business.name,
        "phone_number": business.phone_number,
        "timezone": business.timezone,
    }


# ---- List businesses ----
@router.get("/")
def list_businesses(db: Session = Depends(get_db)):
    return db.query(Business).all()