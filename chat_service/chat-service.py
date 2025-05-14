import os
import jwt
import json
from functools import wraps
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Pretty JSON Middleware
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

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

# Token validation decorator
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

@app.get("/messages")
@token_required
async def get_messages(request: Request):
    user = request.state.user
    user_id = user["sub"]

    # Dummy messages
    messages = [
        {"from": "user2", "to": user_id, "content": "Hello from user2"},
        {"from": "user3", "to": user_id, "content": "Hey there!"}
    ]
    return {"user_id": user_id, "messages": messages}
