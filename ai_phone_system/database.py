from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# -----------------------------
# SESSION HANDLER
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# BUSINESS HOURS
# -----------------------------
def get_business_hours(db, business_id, day_of_week):
    query = text("""
        SELECT start_time, end_time
        FROM business_hours
        WHERE business_id = :business_id
        AND day_of_week = :day_of_week
    """)
    return db.execute(query, {
        "business_id": business_id,
        "day_of_week": day_of_week
    }).fetchone()


# -----------------------------
# PROVIDER HOURS
# -----------------------------
def get_provider_hours(db, provider_id, day_of_week):
    query = text("""
        SELECT start_time, end_time
        FROM provider_hours
        WHERE provider_id = :provider_id
        AND day_of_week = :day_of_week
    """)
    return db.execute(query, {
        "provider_id": provider_id,
        "day_of_week": day_of_week
    }).fetchone()


# -----------------------------
# SERVICE INFO
# -----------------------------
def get_service(db, service_id):
    query = text("""
        SELECT duration_minutes
        FROM services
        WHERE id = :service_id
    """)
    return db.execute(query, {
        "service_id": service_id
    }).fetchone()


# -----------------------------
# EXISTING APPOINTMENTS
# -----------------------------
def get_appointments(db, provider_id, date):
    query = text("""
        SELECT start_time, end_time
        FROM appointments
        WHERE provider_id = :provider_id
        AND date = :date
    """)
    return db.execute(query, {
        "provider_id": provider_id,
        "date": date
    }).fetchall()


# -----------------------------
# CREATE APPOINTMENT
# -----------------------------
def create_appointment(db, data):
    query = text("""
        INSERT INTO appointments (
            id, provider_id, service_id, date,
            start_time, end_time, customer_name, customer_phone
        )
        VALUES (
            :id, :provider_id, :service_id, :date,
            :start_time, :end_time, :customer_name, :customer_phone
        )
    """)

    db.execute(query, data)
    db.commit()
    return True