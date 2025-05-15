import os
import jwt
import json
from functools import wraps
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel  # Added for response modeling

app = FastAPI()

# Response Model
class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    username: str
    full_profile: dict

# Pretty JSON Middleware (Optimized)
@app.middleware("http")
async def prettify_response(request: Request, call_next):
    response = await call_next(request)
    
    if response.media_type == "application/json":
        try:
            content = json.loads(response.body.decode())
            pretty_content = json.dumps(content, indent=2)
            return JSONResponse(
                content=json.loads(pretty_content),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            app.logger.error(f"JSON prettify error: {str(e)}")
    return response

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

# Enhanced Token Validation
def token_required(f):
    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header missing or invalid"
            )

        try:
            token = auth_header.split(" ")[1]
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.state.user = decoded_token
            
            # Validate required claims
            if "sub" not in decoded_token:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token: missing subject claim"
                )
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}"
            )

        return await f(request, *args, **kwargs)
    return decorated_function

@app.get("/user-profile", response_model=UserProfileResponse)
@token_required
async def user_profile(request: Request):
    """
    Returns complete user profile from JWT claims
    """
    user = request.state.user
    
    # Essential validation
    if not isinstance(user, dict):
        raise HTTPException(
            status_code=400,
            detail="Invalid user data in token"
        )
    
    return {
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "username": user.get("username"),
        "full_profile": user
    }

# Enhanced Error Handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body,
            "custom_message": "Validation failed"
        },
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": ["auth", "user", "database"],
        "timestamp": datetime.utcnow().isoformat()
    }