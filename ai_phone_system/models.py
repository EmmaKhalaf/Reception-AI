from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    business_id = Column(Integer, ForeignKey("businesses.id"))

    business = relationship("Business", back_populates="owner")

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    description = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    open_hours = Column(String, nullable=True)  # JSON string

    owner = relationship("User", back_populates="business")

class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    day_of_week = Column(String, nullable=False)  # "mon", "tue", etc.
    start_time = Column(String, nullable=False)   # "09:00"
    end_time = Column(String, nullable=False)     # "17:00"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    date = Column(String, nullable=False)         # "2026-02-05"
    start_time = Column(String, nullable=False)   # "14:00"
    end_time = Column(String, nullable=False)     # "15:00"

