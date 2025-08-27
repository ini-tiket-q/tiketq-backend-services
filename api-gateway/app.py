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
        print(f"DEBUG: No token provided")
        return False

    url = f"{AUTH_SERVICE_URL}/auth/verify-token"
    print(f"DEBUG: Verifying token with {url}")
    print(f"DEBUG: Token: {token[:20]}...")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json={"token": token}, timeout=5)
            print(f"DEBUG: Auth service response: {resp.status_code}")
            print(f"DEBUG: Auth service response body: {resp.text}")
            return resp.status_code == 200
        except httpx.RequestError as e:
            print(f"DEBUG: Request error: {e}")
            return False

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path.lower()
    print(f"DEBUG: Processing request to path: {path}")

    # Check if request path starts with any public route prefix
    if any(path.startswith(route) for route in PUBLIC_ROUTES):
        print(f"DEBUG: Public route, skipping auth")
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    print(f"DEBUG: Auth header: {auth_header}")
    
    token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        print(f"DEBUG: Extracted token: {token[:20]}...")

    if not token:
        print(f"DEBUG: No valid token found")
        return Response(content="Unauthorized - No token", status_code=401)
        
    is_valid = await verify_token(token)
    print(f"DEBUG: Token validation result: {is_valid}")
    
    if not is_valid:
        print(f"DEBUG: Token validation failed")
        return Response(content="Unauthorized - Invalid token", status_code=401)

    print(f"DEBUG: Authentication successful, proceeding to service")
    return await call_next(request)

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(full_path: str, request: Request):
    """
    Generic route to forward all requests to matching services.
    """
    return await forward_request(request, full_path)
