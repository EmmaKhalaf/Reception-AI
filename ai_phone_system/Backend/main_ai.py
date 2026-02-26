from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import twilio, vapi, appointments,business
from app.database import engine
from app.models import business, appointment
from app.database import Base
from app.routes import availability
from app.routes import appointments
Base.metadata.create_all(bind=engine)
from app.routes import auth
from app.routes import business
from app.routes import services
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
app.include_router(twilio.router, prefix="/twilio", tags=["Twilio"])
app.include_router(vapi.router, prefix="/vapi", tags=["Vapi"])
app.include_router(appointments.router,prefix="/appointments",tags=["Appointments"])
app.include_router(business.router,prefix="/businesses",tags=["Businesses"])
app.include_router(availability.router)
app.include_router(appointments.router)
app.include_router(auth.router)
app.include_router(business.router)
app.include_router(services.router)
# ---------------------------------------------------------
# ROUTERS (we will add files gradually)
# ---------------------------------------------------------

# from app.routes import auth, twilio, vapi, appointments
# app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(twilio.router, prefix="/twilio", tags=["Twilio"])
# app.include_router(vapi.router, prefix="/vapi", tags=["Vapi"])
# app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])

# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Reception AI backend running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}