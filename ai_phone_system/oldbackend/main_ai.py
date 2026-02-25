from fastapi import FastAPI, Request
from fastapi.responses import Response, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import psycopg2
import os
import requests
import time   # You need this for token expiration

# ============================================================
# OUTLOOK TOKEN STORAGE (EMPTY AT START)
# ============================================================

OUTLOOK_TOKENS = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": None
}

# DO NOT assign token_data here — it does NOT exist yet.
# Tokens will be filled inside the OAuth callback.

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# DATABASE CONNECTION (optional for now)
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    print("Connected to PostgreSQL successfully.")
except Exception as e:
    print("Database connection failed:", e)

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
# TWILIO WEBHOOK
# ============================================================
#
# @app.post("/twilio/voice")
# async def twilio_voice(request: Request):
#     twiml = """
#     <Response>
#         <Say voice="alice">Hello! Please hold while I connect you to our AI assistant.</Say>
#         <Pause length="1"/>
#         <Say voice="alice">Goodbye.</Say>
#     </Response>
#     """
#     return Response(content=twiml.strip(), media_type="application/xml")
#
#

# ============================================================
# RUN SERVER (IMPORTANT: PORT 80)
# ============================================================


@app.get("/auth/google")
def google_auth():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=https://www.googleapis.com/auth/calendar"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(google_auth_url)
@app.get("/auth/google/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")

    if not code:
        return JSONResponse({"error": "Missing code"}, status_code=400)

    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=data)
    tokens = token_response.json()

    # TODO: Save tokens in your DB
    # Example:
    # save_calendar_tokens(business_id, tokens)

    return JSONResponse({"message": "Google Calendar connected!", "tokens": tokens})
def availability_google_token(refresh_token: str):
    url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(url, data=data)
    return response.json()
# @app.post("/vapi")
# async def vapi_webhook(request: Request):
#     body = await request.json()
#
#     print("\n--- VAPI EVENT RECEIVED ---")
#     print(json.dumps(body, indent=2))
#     print("--- END EVENT ---\n")
#
#     if body.get("type") == "tool.call":
#         tool_name = body["tool"]
#         args = body["arguments"]
#
#         handler = TOOL_HANDLERS.get(tool_name)
#
#         if handler:
#             result = await handler(args)
#
#             print("\n--- TOOL RESPONSE ---")
#             print(json.dumps(result, indent=2))
#             print("--- END TOOL RESPONSE ---\n")
#
#             return {
#                 "tool": tool_name,
#                 "result": result
#             }
#
#     return {"status": "ok"}
# import asyncpg
# import os

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
@app.on_event("startup")
async def startup_event():
    await init_db()
from fastapi import FastAPI, Depends
from datetime import datetime, time, timedelta
import uuid

from database import (
    get_db,
    get_business_hours,
    get_provider_hours,
    get_service,
    get_appointments,
    create_appointment
)

app = FastAPI()


# ---------------------------------------------------------
# TIME SLOT GENERATOR
# ---------------------------------------------------------
def generate_time_slots(start: time, end: time, interval_minutes: int = 15):
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_dt = datetime.combine(datetime.today(), end)

    while current + timedelta(minutes=interval_minutes) <= end_dt:
        slots.append(current.time())
        current += timedelta(minutes=interval_minutes)

    return slots


# ---------------------------------------------------------
# AVAILABILITY ENGINE
# ---------------------------------------------------------
def calculate_availability(business_hours, provider_hours, service_duration, appointments):
    # Intersect business + provider hours
    start = max(business_hours.start_time, provider_hours.start_time)
    end = min(business_hours.end_time, provider_hours.end_time)

    # Generate 15-minute slots
    slots = generate_time_slots(start, end, 15)
    available = []

    for slot in slots:
        slot_start = datetime.combine(datetime.today(), slot)
        slot_end = slot_start + timedelta(minutes=service_duration)

        # Slot must fit inside working hours
        if slot_end.time() > end:
            continue

        # Check for conflicts
        conflict = False
        for appt in appointments:
            appt_start = datetime.combine(datetime.today(), appt.start_time)
            appt_end = datetime.combine(datetime.today(), appt.end_time)

            if not (slot_end <= appt_start or slot_start >= appt_end):
                conflict = True
                break

        if not conflict:
            available.append(slot.strftime("%H:%M"))

    return available


@app.post("/availability")
def availability(payload: dict, request: Request, db=Depends(get_db)):
    business_id = payload["business_id"]
    provider_id = payload["provider_id"]
    service_id = payload["service_id"]
    date = payload["date"]

    # Convert date → weekday number
    day_of_week = datetime.strptime(date, "%Y-%m-%d").weekday()

    business_hours = get_business_hours(db, business_id, day_of_week)
    provider_hours = get_provider_hours(db, provider_id, day_of_week)
    service = get_service(db, service_id)
    appointments = get_appointments(db, provider_id, date)

    if not business_hours or not provider_hours:
        return {"available_slots": []}

    # Build ISO start/end for the day
    start_iso = f"{date}T00:00:00Z"
    end_iso = f"{date}T23:59:59Z"

    # ---------------------------------------------------------
    # OUTLOOK BUSY TIMES
    # ---------------------------------------------------------
    outlook_token = get_valid_outlook_token()

    if outlook_token:
        outlook_busy = get_outlook_busy_times(
            outlook_token,
            start_iso,
            end_iso
        )

        # Convert Outlook busy blocks into appointment-like objects
        for block in outlook_busy.get("value", []):
            for interval in block.get("scheduleItems", []):
                appointments.append({
                    "start_time": interval["start"]["dateTime"],
                    "end_time": interval["end"]["dateTime"]
                })

    # ---------------------------------------------------------
    # GOOGLE BUSY TIMES
    # ---------------------------------------------------------
    google_token = get_valid_google_token(business_id)

    if google_token:
        google_busy = get_google_busy_times(
            google_token,
            start=start_iso,
            end=end_iso
        )

        for event in google_busy:
            appointments.append({
                "start_time": event["start"],
                "end_time": event["end"]
            })

    # ---------------------------------------------------------
    # CALCULATE FINAL AVAILABILITY
    # ---------------------------------------------------------
    slots = calculate_availability(
        business_hours,
        provider_hours,
        service.duration_minutes,
        appointments
    )

    return {
        "provider_id": provider_id,
        "service_id": service_id,
        "date": date,
        "available_slots": slots
    }
# ---------------------------------------------------------
# BOOKING ENDPOINT
# ---------------------------------------------------------
@app.post("/book")
def book(payload: dict, request: Request, db=Depends(get_db)):
    business_id = payload["business_id"]
    provider_id = payload["provider_id"]
    service_id = payload["service_id"]
    customer_name = payload["customer_name"]
    customer_phone = payload["customer_phone"]
    date = payload["date"]
    start_time = payload["start_time"]  # "14:00"

    # Get service duration
    service = get_service(db, service_id)
    duration = service.duration_minutes

    # Build start/end datetime strings
    start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=duration)

    start_iso = start_dt.isoformat() + "Z"
    end_iso = end_dt.isoformat() + "Z"

    # Save appointment in your DB
    save_appointment(
        db,
        business_id,
        provider_id,
        service_id,
        customer_name,
        customer_phone,
        start_dt,
        end_dt
    )

    # ---------------------------------------------------------
    # GOOGLE CALENDAR EVENT CREATION
    # ---------------------------------------------------------
    access_token = get_valid_google_token(business_id)

    if access_token:
        create_google_event(
            access_token,
            summary=f"{service.name} with {customer_name}",
            start=start_iso,
            end=end_iso
        )

    return {
        "message": "Appointment booked successfully",
        "start": start_iso,
        "end": end_iso
    }
def get_google_busy_times(access_token: str, start: str, end: str):
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    headers = {"Authorization": f"Bearer {access_token}"}

    params = {
        "timeMin": start,
        "timeMax": end,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    response = requests.get(url, headers=headers, params=params)
    events = response.json().get("items", [])

    busy = []
    for event in events:
        if event.get("transparency") != "transparent":
            busy.append({
                "start": event["start"].get("dateTime"),
                "end": event["end"].get("dateTime")
            })

    return busy
def create_google_event(access_token: str, summary: str, start: str, end: str):
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    event = {
        "summary": summary,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }

    response = requests.post(url, headers=headers, json=event)
    return response.json()
from datetime import datetime, timedelta

def save_calendar_tokens(business_id: int, tokens: dict):
    conn = get_db()
    cur = conn.cursor()

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in")

    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    cur.execute("""
        INSERT INTO calendar_integrations (business_id, provider, access_token, refresh_token, expires_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (business_id) DO UPDATE SET
            access_token = EXCLUDED.access_token,
            refresh_token = EXCLUDED.refresh_token,
            expires_at = EXCLUDED.expires_at,
            updated_at = NOW();
    """, (business_id, "google", access_token, refresh_token, expires_at))

    conn.commit()
    cur.close()
    conn.close()
def load_calendar_tokens(business_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT access_token, refresh_token, expires_at
        FROM calendar_integrations
        WHERE business_id = %s AND provider = 'google'
    """, (business_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "access_token": row[0],
        "refresh_token": row[1],
        "expires_at": row[2],
    }
def refresh_google_token(refresh_token: str):
    url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    response = requests.post(url, data=data)
    return response.json()
def get_business_id_from_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("business_id")
    except Exception:
        return None
@app.get("/auth/google/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")

    # Extract business_id from JWT token
    business_id = get_business_id_from_token(request)
    if not business_id:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not code:
        return JSONResponse({"error": "Missing code"}, status_code=400)

    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=data)
    tokens = token_response.json()

    # Save tokens in DB for this business
    save_calendar_tokens(business_id, tokens)

    return JSONResponse({"message": "Google Calendar connected!"})
def create_google_event(access_token: str, summary: str, start: str, end: str):
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    event = {
        "summary": summary,
        "start": {"dateTime": start},
        "end": {"dateTime": end},
    }

    response = requests.post(url, headers=headers, json=event)
    return response.json()
def get_valid_google_token(business_id: int):
    tokens = load_calendar_tokens(business_id)
    if not tokens:
        return None

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    expires_at = tokens["expires_at"]

    # If expired → refresh
    if expires_at < datetime.utcnow():
        new_tokens = refresh_google_token(refresh_token)
        save_calendar_tokens(business_id, new_tokens)
        return new_tokens["access_token"]

    return access_token
@app.get("/auth/outlook/callback")
async def outlook_callback(request: Request):
    code = request.query_params.get("code")

    data = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv("MICROSOFT_REDIRECT_URI"),
    }

    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=data, headers=headers)
    tokens = response.json()

    OUTLOOK_TOKENS["access_token"] = tokens.get("access_token")
    OUTLOOK_TOKENS["refresh_token"] = tokens.get("refresh_token")
    OUTLOOK_TOKENS["expires_at"] = time.time() + tokens.get("expires_in", 3600)

    return JSONResponse({"message": "Outlook connected!"})
def get_outlook_busy_times(access_token, start, end):
    url = "https://graph.microsoft.com/v1.0/me/calendar/getSchedule"

    body = {
        "schedules": ["me"],
        "startTime": {"dateTime": start, "timeZone": "UTC"},
        "endTime": {"dateTime": end, "timeZone": "UTC"},
        "availabilityViewInterval": 30
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=body, headers=headers)
    return response.json()
@app.get("/auth/outlook")
def outlook_auth():
    params = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": os.getenv("MICROSOFT_REDIRECT_URI"),
        "response_mode": "query",
        "scope": "offline_access Calendars.ReadWrite",
    }

    base = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    url = base + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return RedirectResponse(url)
@app.get("/auth/outlook/callback")
async def outlook_callback(request: Request):
    code = request.query_params.get("code")

    data = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": os.getenv("MICROSOFT_REDIRECT_URI"),
    }

    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=data, headers=headers)
    tokens = response.json()

    OUTLOOK_TOKENS["access_token"] = tokens.get("access_token")
    OUTLOOK_TOKENS["refresh_token"] = tokens.get("refresh_token")
    OUTLOOK_TOKENS["expires_at"] = time.time() + tokens.get("expires_in", 3600)

    return JSONResponse({"message": "Outlook connected!"})
def refresh_outlook_token(refresh_token):
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    data = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": os.getenv("MICROSOFT_REDIRECT_URI"),
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_url, data=data, headers=headers)
    return response.json()
def get_valid_outlook_token():
    now = time.time()

    if OUTLOOK_TOKENS["access_token"] is None:
        return None

    if OUTLOOK_TOKENS["expires_at"] and now >= OUTLOOK_TOKENS["expires_at"]:
        refreshed = refresh_outlook_token(OUTLOOK_TOKENS["refresh_token"])
        OUTLOOK_TOKENS["access_token"] = refreshed["access_token"]
        OUTLOOK_TOKENS["refresh_token"] = refreshed["refresh_token"]
        OUTLOOK_TOKENS["expires_at"] = now + refreshed["expires_in"]

    return OUTLOOK_TOKENS["access_token"]
def get_outlook_busy_times(access_token, start, end):
    url = "https://graph.microsoft.com/v1.0/me/calendar/getSchedule"

    body = {
        "schedules": ["me"],
        "startTime": {"dateTime": start, "timeZone": "UTC"},
        "endTime": {"dateTime": end, "timeZone": "UTC"},
        "availabilityViewInterval": 30
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=body, headers=headers)
    return response.json()
def create_outlook_event(access_token, subject, start, end):
    url = "https://graph.microsoft.com/v1.0/me/events"

    event = {
        "subject": subject,
        "start": {"dateTime": start, "timeZone": "UTC"},
        "end": {"dateTime": end, "timeZone": "UTC"},
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=event, headers=headers)
    return response.json()
@app.get("/")
def home():
    return {"status": "ok", "message": "Reception AI is running"}
