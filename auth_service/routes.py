from fastapi import APIRouter, HTTPException
from models import User, LoginRequest
from utils import hash_password, verify_password, create_access_token
from motor.motor_asyncio import AsyncIOMotorClient
import os
from passlib.hash import bcrypt


auth_router = APIRouter()
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client["chat_app"]
users_collection = db["users"]

@auth_router.post("/register")
async def register(user: User):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user.password = hash_password(user.password)
    await users_collection.insert_one(user.dict())
    return {"message": "User registered successfully"}


@auth_router.post("/login")
async def login(login_req: LoginRequest):
    user = await users_collection.find_one({"email": login_req.email})
    if not user or not verify_password(login_req.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    payload = {
        "sub": str(user['_id']),  # subject (usually user ID)
        "email": user["email"],    # email field
        "username": user.get("username", "")  # optional: include username too
    }

    token = create_access_token(payload)
    return {"access_token": token, "token_type": "bearer"}
