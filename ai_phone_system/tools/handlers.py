# tools/handlers.py

TOOL_HANDLERS = {}

def tool(name):
    def decorator(func):
        TOOL_HANDLERS[name] = func
        return func
    return decorator


@tool("checkAvailability")
async def handle_check_availability(args):
    provider = args["provider"]
    date = args["date"]

    # Example logic
    return {
        "times": ["10:30 AM", "2:15 PM", "4:00 PM"]
    }


@tool("bookAppointment")
async def handle_book_appointment(args):
    provider = args["provider"]
    date = args["date"]
    time = args["time"]
    patient = args["patientName"]

    confirmation_id = f"{provider}-{date}-{time}".replace(" ", "")

    return {
        "confirmationId": confirmation_id,
        "status": "confirmed"
    }
def get_business_id_from_phone(phone_number: str):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM businesses
        WHERE phone_number = %s
        LIMIT 1
    """, (phone_number,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    return None

def handle_tool_call(request):
    data = request.json()

    # Extract the Twilio number the caller dialed
    called_number = data.get("metadata", {}).get("called")

    # Get the business_id from the database
    business_id = get_business_id_from_phone(called_number)

    if not business_id:
        return {"error": "Business not found"}

    # Now pass business_id into your logic
    tool_name = data.get("tool")
    args = data.get("arguments", {})