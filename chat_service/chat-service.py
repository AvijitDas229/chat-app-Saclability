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

# === FastAPI app ===
app = FastAPI()

# === MongoDB connection ===
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/chatdb")
client = MongoClient(MONGO_URI)
db = client["chatdb"]
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
    return {"message": "Message sent successfully"}

# === GET /chat/messages?other_user_email=... ===
@app.get("/chat/messages")
@token_required
async def get_messages(request: Request, other_user_email: str):
    user_email = request.state.user.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="Email not found in token")

    print(f"🔍 Logged-in user_email: {user_email}")
    print(f"🔍 Request param: other_user_email = {other_user_email}")

    print("=== All messages in DB ===")
    for msg in messages_collection.find():
        print(msg)

    query = {"$or": []}
    if other_user_email:
        query["$or"].extend([
            {"sender_email": user_email, "receiver_email": other_user_email},
            {"sender_email": other_user_email, "receiver_email": user_email}
        ])
    else:
        query["$or"].extend([
            {"sender_email": user_email},
            {"receiver_email": user_email}
        ])


    messages = list(messages_collection.find(query).sort("timestamp", 1))
    result = []
    for msg in messages:
        result.append({
            "id": str(msg["_id"]),
            "from": msg["sender_email"],
            "to": msg["receiver_email"],
            "message": msg["message"],
            "timestamp": msg["timestamp"].isoformat() if msg.get("timestamp") else "",
            "read": msg.get("read", False)
        })
    return {"messages": result}

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

