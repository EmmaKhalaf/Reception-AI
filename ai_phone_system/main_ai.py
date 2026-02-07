import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="Emma AI Backend")

# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
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
# TEMPORARY IN-MEMORY STORAGE (replace with DB later)
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

FAKE_APPOINTMENTS = []
NEXT_APPOINTMENT_ID = 1

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
# BOOKING
# ============================================================

@app.post("/book", response_model=BookingResponse)
def book_appointment(req: BookingRequest):
    global NEXT_APPOINTMENT_ID

    appointment = {
        "id": NEXT_APPOINTMENT_ID,
        "customer_name": req.customer_name,
        "customer_phone": req.customer_phone,
        "service": req.service,
        "date": req.date,
        "time": req.time,
    }

    FAKE_APPOINTMENTS.append(appointment)
    NEXT_APPOINTMENT_ID += 1

    return BookingResponse(
        success=True,
        message="Appointment booked successfully.",
        appointment_id=appointment["id"],
    )

# ============================================================
# CANCEL APPOINTMENT
# ============================================================

@app.post("/appointment/cancel", response_model=CancelResponse)
def cancel_appointment(req: CancelRequest):
    for appt in FAKE_APPOINTMENTS:
        if appt["customer_phone"] == req.customer_phone:
            FAKE_APPOINTMENTS.remove(appt)
            return CancelResponse(success=True, message="Appointment cancelled.")
    return CancelResponse(success=False, message="No appointment found.")

# ============================================================
# RESCHEDULE APPOINTMENT
# ============================================================

@app.post("/appointment/reschedule", response_model=RescheduleResponse)
def reschedule_appointment(req: RescheduleRequest):
    for appt in FAKE_APPOINTMENTS:
        if appt["customer_phone"] == req.customer_phone:
            appt["date"] = req.new_date
            appt["time"] = req.new_time
            return RescheduleResponse(success=True, message="Appointment rescheduled.")
    return RescheduleResponse(success=False, message="No appointment found.")

# ============================================================
# APPOINTMENT DETAILS
# ============================================================

@app.post("/appointment/details", response_model=AppointmentDetailsResponse)
def get_appointment_details(req: AppointmentDetailsRequest):
    for appt in FAKE_APPOINTMENTS:
        if (
            (req.customer_name and appt["customer_name"].lower() == req.customer_name.lower()) or
            (req.customer_phone and appt["customer_phone"] == req.customer_phone)
        ):
            return AppointmentDetailsResponse(
                has_appointment=True,
                date=appt["date"],
                time=appt["time"],
                service=appt["service"]
            )

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

# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)