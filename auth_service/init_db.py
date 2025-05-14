from motor.motor_asyncio import AsyncIOMotorClient

async def init_counter():
    client = AsyncIOMotorClient("mongodb://mongodb:27017")
    db = client["chat_app"]
    counters = db["counters"]
    
    existing = await counters.find_one({"_id": "user_id"})
    if not existing:
        await counters.insert_one({"_id": "user_id", "sequence_value": 0})
