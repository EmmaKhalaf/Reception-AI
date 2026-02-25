from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/")
async def vapi_webhook(request: Request):
    body = await request.json()

    print("\n--- VAPI EVENT RECEIVED ---")
    print(body)
    print("--- END EVENT ---\n")

    # For now, just acknowledge
    return {"status": "ok"}