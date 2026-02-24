from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter()

@router.post("/voice")
async def twilio_voice(request: Request):
    twiml = """
    <Response>
        <Say voice="alice">
            Hello! Please hold while I connect you to our AI assistant.
        </Say>
        <Pause length="1"/>
        <Say voice="alice">Goodbye.</Say>
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")