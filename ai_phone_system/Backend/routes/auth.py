from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import os

from ..database import get_db
from ..models.business import Business

router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("JWT_SECRET", "dev_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
def register_business(
    name: str,
    phone_number: str | None = None,
    timezone: str = "UTC",
    db: Session = Depends(get_db),
):
    business = Business(
        name=name,
        phone_number=phone_number,
        timezone=timezone,
    )

    db.add(business)
    db.commit()
    db.refresh(business)

    token = create_access_token({
        "business_id": business.id
    })

    return {
        "business_id": business.id,
        "access_token": token,
        "token_type": "bearer",
    }