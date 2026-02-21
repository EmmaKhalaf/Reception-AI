import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI(title="Emma AI Backend")
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
# ============================================================
# DATABASE CONNECTION
# ============================================================
DATABASE_URL = os.getenv("DATABASE_URL")


try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    print("Connected to Supabase PostgreSQL successfully.")
except Exception as e:
    print("Database connection failed:", e)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MODELS
# ============================================================

class BusinessInfo(BaseModel):
    name: str
    phone: str
    address: str
    timezone: str
    services: List[str]

class AvailabilityRequest(BaseModel):
    date: str

class AvailabilitySlot(BaseModel):
    start_time: str
    end_time: str

class BookingRequest(BaseModel):
    customer_name: str
    customer_phone: str
    service: str
    date: str
    time: str

class BookingResponse(BaseModel):
    success: bool
    message: str
    appointment_id: Optional[int] = None

class AppointmentDetailsRequest(BaseModel):
    customer_name: str | None = None
    customer_phone: str | None = None

class AppointmentDetailsResponse(BaseModel):
    has_appointment: bool
    date: str | None = None
    time: str | None = None
    service: str | None = None

class SaveNotesRequest(BaseModel):
    customer_name: str
    customer_phone: str | None = None
    notes: str

class SaveNotesResponse(BaseModel):
    success: bool
    message: str

class SMSRequest(BaseModel):
    phone: str
    message: str

class SMSResponse(BaseModel):
    success: bool
    message: str

class CancelRequest(BaseModel):
    customer_phone: str
    customer_name: Optional[str] = None

class CancelResponse(BaseModel):
    success: bool
    message: str

class RescheduleRequest(BaseModel):
    customer_phone: str
    customer_name: Optional[str] = None
    new_date: str
    new_time: str

class RescheduleResponse(BaseModel):
    success: bool
    message: str

class HoursResponse(BaseModel):
    open_hours: str

# ============================================================
# TEMPORARY IN-MEMORY STORAGE
# ============================================================

FAKE_BUSINESS = BusinessInfo(
    name="Emma's Studio",
    phone="+1XXXYYYZZZZ",
    address="123 Example Street, Gatineau, QC",
    timezone="America/Toronto",
    services=["Haircut", "Color", "Styling"],
)

FAKE_HOURS = "Mon–Fri: 9am–6pm, Sat: 10am–4pm, Sun: Closed"

FAKE_AVAILABILITY = {
    "2025-02-05": [
        AvailabilitySlot(start_time="10:00", end_time="10:30"),
        AvailabilitySlot(start_time="11:00", end_time="11:30"),
        AvailabilitySlot(start_time="14:00", end_time="14:30"),
    ]
}

FAKE_NOTES = []
FAKE_SMS_LOG = []

# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}

# ============================================================
# BUSINESS INFO
# ============================================================

@app.get("/business", response_model=BusinessInfo)
def get_business_info():
    return FAKE_BUSINESS

@app.get("/business/hours", response_model=HoursResponse)
def get_business_hours():
    return HoursResponse(open_hours=FAKE_HOURS)

# ============================================================
# AVAILABILITY
# ============================================================

@app.post("/availability", response_model=List[AvailabilitySlot])
def get_availability(req: AvailabilityRequest):
    return FAKE_AVAILABILITY.get(req.date, [])

# ============================================================
# BOOKING (DATABASE)
# ============================================================

@app.post("/book", response_model=BookingResponse)
def book_appointment(req: BookingRequest):
    try:
        cursor.execute(
            """
            insert into appointments (customer_name, customer_phone, service, date, time)
            values (%s, %s, %s, %s, %s)
            returning id;
            """,
            (req.customer_name, req.customer_phone, req.service, req.date, req.time)
        )
        appointment_id = cursor.fetchone()[0]

        return BookingResponse(
            success=True,
            message="Appointment booked successfully.",
            appointment_id=appointment_id
        )

    except Exception as e:
        return BookingResponse(
            success=False,
            message=f"Database error: {e}",
            appointment_id=None
        )

# ============================================================
# CANCEL APPOINTMENT
# ============================================================

@app.post("/appointment/cancel", response_model=CancelResponse)
def cancel_appointment(req: CancelRequest):
    cursor.execute(
        """
        update appointments
        set status = 'cancelled', updated_at = now()
        where customer_phone = %s and status = 'scheduled'
        returning id;
        """,
        (req.customer_phone,)
    )

    row = cursor.fetchone()

    if row:
        return CancelResponse(success=True, message="Appointment cancelled.")
    return CancelResponse(success=False, message="No appointment found.")

# ============================================================
# RESCHEDULE APPOINTMENT
# ============================================================

@app.post("/appointment/reschedule", response_model=RescheduleResponse)
def reschedule_appointment(req: RescheduleRequest):
    cursor.execute(
        """
        update appointments
        set date = %s, time = %s, updated_at = now()
        where customer_phone = %s and status = 'scheduled'
        returning id;
        """,
        (req.new_date, req.new_time, req.customer_phone)
    )

    row = cursor.fetchone()

    if row:
        return RescheduleResponse(success=True, message="Appointment rescheduled.")
    return RescheduleResponse(success=False, message="No appointment found.")

# ============================================================
# APPOINTMENT DETAILS
# ============================================================

@app.post("/appointment/details", response_model=AppointmentDetailsResponse)
def get_appointment_details(req: AppointmentDetailsRequest):
    try:
        cursor.execute(
            """
            select date, time, service
            from appointments
            where 
                (lower(customer_name) = lower(%s) or %s is null)
                and (customer_phone = %s or %s is null)
                and status = 'scheduled'
            limit 1;
            """,
            (req.customer_name, req.customer_name, req.customer_phone, req.customer_phone)
        )

        row = cursor.fetchone()

        if row:
            return AppointmentDetailsResponse(
                has_appointment=True,
                date=str(row[0]),
                time=row[1],
                service=row[2]
            )

        return AppointmentDetailsResponse(
            has_appointment=False,
            date=None,
            time=None,
            service=None
        )

    except Exception:
        return AppointmentDetailsResponse(
            has_appointment=False,
            date=None,
            time=None,
            service=None
        )

# ============================================================
# SAVE NOTES
# ============================================================

@app.post("/notes/save", response_model=SaveNotesResponse)
def save_caller_notes(req: SaveNotesRequest):
    FAKE_NOTES.append({
        "customer_name": req.customer_name,
        "customer_phone": req.customer_phone,
        "notes": req.notes
    })
    return SaveNotesResponse(success=True, message="Notes saved successfully.")

# ============================================================
# SEND SMS
# ============================================================

@app.post("/sms/send", response_model=SMSResponse)
def send_sms(req: SMSRequest):
    FAKE_SMS_LOG.append({"phone": req.phone, "message": req.message})
    return SMSResponse(success=True, message="SMS sent (simulated).")

# ============================================================
# VAPI WEBHOOK
# ============================================================

@app.post("/vapi")
async def vapi_webhook(request: Request):
    body = await request.json()
    print("Vapi event:", body)
    return {"status": "ok"}

# ============================================================
# TWILIO WEBHOOK
# ============================================================

@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    twiml = """
    <Response>
        <Say voice="alice">Hello! Please hold while I connect you to our AI assistant.</Say>
        <Pause length="1"/>
        <Say voice="alice">Goodbye.</Say>
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")
Base.metadata.create_all(bind=engine)
# ============================================================
# RUN SERVER (IMPORTANT: PORT 80)
# ============================================================
from fastapi import FastAPI, Request
import json
from tools.handlers import TOOL_HANDLERS

app = FastAPI()


@app.post("/vapi")
async def vapi_webhook(request: Request):
    body = await request.json()

    print("\n--- VAPI EVENT RECEIVED ---")
    print(json.dumps(body, indent=2))
    print("--- END EVENT ---\n")

    if body.get("type") == "tool.call":
        tool_name = body["tool"]
        args = body["arguments"]

        handler = TOOL_HANDLERS.get(tool_name)

        if handler:
            result = await handler(args)

            print("\n--- TOOL RESPONSE ---")
            print(json.dumps(result, indent=2))
            print("--- END TOOL RESPONSE ---\n")

            return {
                "tool": tool_name,
                "result": result
            }

    return {"status": "ok"}
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            provider TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            patient_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    await conn.close()
from datetime import datetime, time, timedelta
import database as db

def generate_time_slots(start: time, end: time, interval_minutes: int = 15):
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)

    while current + timedelta(minutes=interval_minutes) <= end_dt:
        slots.append(current.time())
        current += timedelta(minutes=interval_minutes)

    return slots


def calculate_availability(business_hours, provider_hours, service_duration, appointments):
    start = max(business_hours["start_time"], provider_hours["start_time"])
    end = min(business_hours["end_time"], provider_hours["end_time"])

    slots = generate_time_slots(start, end, 15)
    available = []

    for slot in slots:
        slot_start = datetime.combine(datetime.today(), slot)
        slot_end = slot_start + timedelta(minutes=service_duration)

        if slot_end.time() > end:
            continue

        conflict = False
        for appt in appointments:
            appt_start = datetime.combine(datetime.today(), appt["start_time"])
            appt_end = datetime.combine(datetime.today(), appt["end_time"])

            if not (slot_end <= appt_start or slot_start >= appt_end):
                conflict = True
                break

        if not conflict:
            available.append(slot.strftime("%H:%M"))

    return available
@app.post("/availability")
def availability(payload: dict):
    business_id = payload["business_id"]
    provider_id = payload["provider_id"]
    service_id = payload["service_id"]
    date = payload["date"]

    day_of_week = datetime.strptime(date, "%Y-%m-%d").weekday()

    business_hours = db.get_business_hours(business_id, day_of_week)
    provider_hours = db.get_provider_hours(provider_id, day_of_week)
    service = db.get_service(service_id)
    appointments = db.get_appointments(provider_id, date)

    slots = calculate_availability(
        business_hours,
        provider_hours,
        service["duration_minutes"],
        appointments
    )

    return {
        "provider_id": provider_id,
        "service_id": service_id,
        "date": date,
        "available_slots": slots
    }
@app.post("/book")
def book(payload: dict):
    availability = availability({
        "business_id": payload["business_id"],
        "provider_id": payload["provider_id"],
        "service_id": payload["service_id"],
        "date": payload["date"]
    })

    if payload["time"] not in availability["available_slots"]:
        return {"error": "Time slot not available"}

    appointment_id = str(uuid.uuid4())

    db.create_appointment({
        "id": appointment_id,
        "provider_id": payload["provider_id"],
        "service_id": payload["service_id"],
        "date": payload["date"],
        "start_time": payload["time"],
        "end_time": payload["time"],  # you will calculate end_time later
        "customer_name": payload["customer_name"],
        "customer_phone": payload["customer_phone"]
    })

    return {
        "status": "confirmed",
        "appointment_id": appointment_id
    }
@app.on_event("startup")
async def startup_event():
    await init_db()
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=80)