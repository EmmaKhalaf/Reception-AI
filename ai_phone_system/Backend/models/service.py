from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


def uuid_str():
    return str(uuid.uuid4())


class Service(Base):
    __tablename__ = "services"

    id = Column(String, primary_key=True, default=uuid_str)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)

    name = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=True)

    business = relationship("Business", back_populates="services")