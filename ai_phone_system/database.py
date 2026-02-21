from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
def get_business_hours(business_id, day_of_week):
    # Query your business_hours table
    return db.fetch_one("""
        SELECT start_time, end_time
        FROM business_hours
        WHERE business_id = %s AND day_of_week = %s
    """, (business_id, day_of_week))


def get_provider_hours(provider_id, day_of_week):
    return db.fetch_one("""
        SELECT start_time, end_time
        FROM provider_hours
        WHERE provider_id = %s AND day_of_week = %s
    """, (provider_id, day_of_week))


def get_service(service_id):
    return db.fetch_one("""
        SELECT duration_minutes
        FROM services
        WHERE id = %s
    """, (service_id,))


def get_appointments(provider_id, date):
    return db.fetch_all("""
        SELECT start_time, end_time
        FROM appointments
        WHERE provider_id = %s AND date = %s
    """, (provider_id, date))


def create_appointment(data):
    return db.insert("""
        INSERT INTO appointments (id, provider_id, service_id, date, start_time, end_time, customer_name, customer_phone)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["id"],
        data["provider_id"],
        data["service_id"],
        data["date"],
        data["start_time"],
        data["end_time"],
        data["customer_name"],
        data["customer_phone"]
    ))