from sqlalchemy import Column, String, DateTime, Time, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


def uuid_str():
    return str(uuid.uuid4())


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True, default=uuid_str)

    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    timezone = Column(String, default="UTC")

    created_at = Column(DateTime, default=datetime.utcnow)

    hours = relationship(
        "BusinessHours",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    services = relationship(
        "Service",
        back_populates="business",
        cascade="all, delete-orphan"
    )

    appointments = relationship(
        "Appointment",
        back_populates="business",
        cascade="all, delete-orphan"
    )


class BusinessHours(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)

    day_of_week = Column(Integer, nullable=False)  # 0 = Mon, 6 = Sun
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)

    business = relationship("Business", back_populates="hours")