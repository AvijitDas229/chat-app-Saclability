from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from routes import auth_router
import json

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

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Auth Service is running"}
