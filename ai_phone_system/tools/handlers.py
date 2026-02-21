TOOL_HANDLERS = {}

def tool(name):
    def decorator(func):
        TOOL_HANDLERS[name] = func
        return func
    return decorator

@tool("checkAvailability")
async def handle_check_availability(args):
    return {
        "times": ["10:30 AM", "2:15 PM"]
    }

@tool("bookAppointment")
async def handle_book_appointment(args):
    return {
        "confirmationId": "ABC123",
        "status": "confirmed"
    }