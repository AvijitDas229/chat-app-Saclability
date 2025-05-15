from pydantic import BaseModel, EmailStr


class User(BaseModel):
    email: EmailStr
    username: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterModel(BaseModel):
    username: str
    email: EmailStr
    password: str
