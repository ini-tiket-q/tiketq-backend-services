import os
from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from pathlib import Path
import httpx

from utils.forwarder import forward_request

# Load .env from root directory
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

app = FastAPI()

PUBLIC_ROUTES = {
    "/auth/login",
    "/auth/register",
    "/auth/verify-token",
}

# Load auth service URL
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

async def verify_token(token: str) -> bool:
    """
    Verify the access token with the auth-service.
    """
    if not token:
        return False

    url = f"{AUTH_SERVICE_URL}/verify-token"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"token": token}, timeout=5)
            return resp.status_code == 200
        except httpx.RequestError:
            return False

# @app.middleware("http")
# async def auth_middleware(request: Request, call_next):
#     path = request.url.path.lower()
# 
#     # Check if request path starts with any public route prefix
#     if any(path.startswith(route) for route in PUBLIC_ROUTES):
#         return await call_next(request)
# 
#     auth_header = request.headers.get("Authorization")
#     token = None
#     if auth_header and auth_header.lower().startswith("bearer "):
#         token = auth_header.split(" ", 1)[1].strip()
# 
#     if not token or not await verify_token(token):
#         return Response(content="Unauthorized", status_code=401)
# 
#     return await call_next(request)


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(full_path: str, request: Request):
    """
    Generic route to forward all requests to matching services.
    """
    return await forward_request(request, full_path)
