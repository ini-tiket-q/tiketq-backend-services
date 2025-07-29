import os
from fastapi import FastAPI, Request, Response
from dotenv import load_dotenv
from pathlib import Path
import httpx

from utils.forwarder import forward_request

# Load .env from root directory
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

app = FastAPI()

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

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Middleware to check token before routing request.
    Skip for login/register routes.
    """
    path = request.url.path

    # Public routes — no token required
    if path.startswith("/auth/login") or path.startswith("/auth/register"):
        return await call_next(request)

    # Extract Bearer token
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header and " " in auth_header else None

    # Validate with auth-service
    is_valid = await verify_token(token)
    if not is_valid:
        return Response(content="Unauthorized", status_code=401)

    return await call_next(request)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(full_path: str, request: Request):
    """
    Generic route to forward all requests to matching services.
    """
    return await forward_request(request, full_path)
