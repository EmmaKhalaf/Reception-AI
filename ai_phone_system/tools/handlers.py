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