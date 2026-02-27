# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routes import twilio, vapi, appointments, business, availability, auth, services
from app.models import business as business_model, appointment as appointment_model

# Create tables
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------
# APP
# ---------------------------------------------------------
app = FastAPI(
    title="Reception AI",
    version="0.1.0"
)

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------
app.include_router(twilio.router, prefix="/twilio", tags=["Twilio"])
app.include_router(vapi.router, prefix="/vapi", tags=["Vapi"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
app.include_router(business.router, prefix="/businesses", tags=["Businesses"])
app.include_router(availability.router, prefix="/availability", tags=["Availability"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(services.router, prefix="/services", tags=["Services"])

# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "Reception AI backend running"}

@app.get("/health")
def health():
    return {"status": "healthy"}