from sqlalchemy import Column, String, DateTime, ForeignKey
from datetime import datetime
import uuid

from app.database import Base


def uuid_str():
    return str(uuid.uuid4())


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=uuid_str)

    business_id = Column(
        String,
        ForeignKey("businesses.id"),
        nullable=False
    )

    customer_name = Column(String, nullable=False)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)