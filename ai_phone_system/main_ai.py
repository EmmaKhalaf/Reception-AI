from fastapi import FastAPI, Request, Depends
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="Emma AI Backend")

# ----- CORS (so your future frontend can talk to this API) -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Models -----

class BusinessInfo(BaseModel):
    name: str
    phone: str
    address: str
    timezone: str
    services: List[str]

class AvailabilityRequest(BaseModel):
    date: str  # e.g. "2025-02-05"

class AvailabilitySlot(BaseModel):
    start_time: str  # "14:00"
    end_time: str    # "14:30"

class BookingRequest(BaseModel):
    customer_name: str
    customer_phone: str
    service: str
    date: str        # "2025-02-05"
    time: str        # "14:00"

class BookingResponse(BaseModel):
    success: bool
    message: str
    appointment_id: Optional[int] = None

# ----- In-memory fake storage (replace with your DB) -----

FAKE_BUSINESS = BusinessInfo(
    name="Emma's Studio",
    phone="+1XXXYYYZZZZ",
    address="123 Example Street, Gatineau, QC",
    timezone="America/Toronto",
    services=["Haircut", "Color", "Styling"],
)

FAKE_AVAILABILITY = {
    "2025-02-05": [
        AvailabilitySlot(start_time="10:00", end_time="10:30"),
        AvailabilitySlot(start_time="11:00", end_time="11:30"),
        AvailabilitySlot(start_time="14:00", end_time="14:30"),
    ]
}

FAKE_APPOINTMENTS = []
NEXT_APPOINTMENT_ID = 1


# ----- Health check -----

@app.get("/health")
def health():
    return {"status": "ok"}


# ----- Business info -----

@app.get("/business", response_model=BusinessInfo)
def get_business_info():
    return FAKE_BUSINESS


# ----- Availability -----

@app.post("/availability", response_model=List[AvailabilitySlot])
def get_availability(req: AvailabilityRequest):
    return FAKE_AVAILABILITY.get(req.date, [])


# ----- Booking -----

@app.post("/book", response_model=BookingResponse)
def book_appointment(req: BookingRequest):
    global NEXT_APPOINTMENT_ID

    # Here you would:
    # 1. Check if slot is free in DB
    # 2. Save appointment
    # 3. Maybe send SMS/email

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


# ----- Twilio voice webhook (basic placeholder) -----

@app.post("/twilio/voice")
async def twilio_voice(request: Request):
    """
    Twilio will POST here when someone calls your number.
    This version just plays a simple message.
    Later, you can swap this to VAPI or your own AI flow.
    """
    twiml = """
    <Response>
        <Say voice="alice">Hello! Please hold while I connect you to our AI assistant.</Say>
        <Pause length="1"/>
        <Say voice="alice">Goodbye.</Say>
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")


# ----- Optional: endpoint VAPI can call as a "tool" -----

@app.post("/vapi/book", response_model=BookingResponse)
def vapi_book(req: BookingRequest):
    """
    Same as /book, but you can point a VAPI tool here.
    """
    return book_appointment(req)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
