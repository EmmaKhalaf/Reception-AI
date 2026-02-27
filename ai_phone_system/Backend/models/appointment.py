from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


def uuid_str():
    return str(uuid.uuid4())


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=uuid_str)

    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)

    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    status = Column(String, default="scheduled")  # scheduled, cancelled, completed

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationship back to Business
    business = relationship("Business", back_populates="appointments")