import asyncio
import json
from services.booking_service import BookingService

async def check_list():
    user_id = 'e2867f01-6e68-44da-9f30-56443add56df'
    print(f"Listing bookings for user: {user_id}")
    res = await BookingService.list_customer_bookings(user_id)
    print(f"Found {len(res)} bookings.")
    if res:
        print(f"First booking: {json.dumps(res[0], indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(check_list())
