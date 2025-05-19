import os
import jwt
import json
from functools import wraps
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson.objectid import ObjectId
from pydantic import BaseModel
from messaging.producer import send_message_to_queue  # ✅ RabbitMQ producer import

# === FastAPI app ===
app = FastAPI()

# === MongoDB connection ===
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/chat_app")
client = MongoClient(MONGO_URI)
db = client["chat_app"]
messages_collection = db["messages"]

# === Secret Key ===
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

# === Pretty JSON Middleware ===
@app.middleware("http")
async def prettify_response(request: Request, call_next):
    response = await call_next(request)
    if response.media_type == "application/json":
        raw_body = b""
        async for chunk in response.body_iterator:
            raw_body += chunk
        try:
            parsed = json.loads(raw_body.decode())
            pretty = json.dumps(parsed, indent=2)
            return JSONResponse(content=json.loads(pretty), status_code=response.status_code)
        except Exception:
            pass
    return response

# === JWT Auth Decorator ===
def token_required(f):
    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Token is missing")
        try:
            token = token.split(" ")[1]
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.state.user = decoded_token
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        return await f(request, *args, **kwargs)
    return decorated_function

# === Pydantic Models ===
class SendMessage(BaseModel):
    receiver_email: str
    message: str

class MarkRead(BaseModel):
    message_id: str

# === POST /chat/send ===
@app.post("/chat/send")
@token_required
async def send_message(request: Request, body: SendMessage):
    sender_email = request.state.user.get("email")
    if not sender_email:
        raise HTTPException(status_code=400, detail="Email not found in token")

    message_doc = {
        "sender_email": sender_email,
        "receiver_email": body.receiver_email,
        "message": body.message,
        "timestamp": datetime.utcnow(),
        "read": False
    }
    result = messages_collection.insert_one(message_doc)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to send message")

    # ✅ Send message to RabbitMQ
    send_message_to_queue({
        "sender_email": sender_email,
        "receiver_email": body.receiver_email,
        "message": body.message,
        "timestamp": message_doc["timestamp"].isoformat()
    })

    return {"message": "Message sent successfully"}

# === GET /chat/messages?other_user_email=... ===
@app.get("/chat/messages")
@token_required
async def get_messages(request: Request, other_user_email: str):
    try:
        user_email = request.state.user.get("email")
        if not user_email:
            return JSONResponse(
                status_code=400,
                content={"messages": [], "error": "Email not found in token"}
            )

        print(f"🔍 User making request: {user_email}")
        print(f"🔍 Looking for messages with: {other_user_email}")

        query = {
            "$or": [
                {"sender_email": user_email, "receiver_email": other_user_email},
                {"sender_email": other_user_email, "receiver_email": user_email}
            ]
        }
        print(f"🔍 MongoDB query: {query}")

        total_messages = messages_collection.count_documents({})
        matching_messages = messages_collection.count_documents(query)
        print(f"🔍 Total messages in collection: {total_messages}")
        print(f"🔍 Matching messages found: {matching_messages}")

        messages = list(messages_collection.find(query).sort("timestamp", 1))

        result = []
        for msg in messages:
            result.append({
                "id": str(msg["_id"]),
                "from": msg["sender_email"],
                "to": msg["receiver_email"],
                "message": msg["message"],
                "timestamp": msg["timestamp"].isoformat() if msg.get("timestamp") else None,
                "read": msg.get("read", False)
            })

        print(f"🔍 Returning {len(result)} messages")
        return {"messages": result}

    except Exception as e:
        print(f"🔥 Error fetching messages: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"messages": [], "error": "Internal server error"}
        )

# === POST /chat/mark_read ===
@app.post("/chat/mark_read")
@token_required
async def mark_message_read(request: Request, body: MarkRead):
    user_email = request.state.user.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="Email not found in token")

    try:
        obj_id = ObjectId(body.message_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid message ID format")

    result = messages_collection.update_one(
        {"_id": obj_id, "receiver_email": user_email},
        {"$set": {"read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found or unauthorized")
    return {"message": "Message marked as read"}
