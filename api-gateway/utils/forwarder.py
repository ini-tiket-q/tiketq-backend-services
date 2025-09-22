import os
import httpx
from fastapi import Request, Response
from urllib.parse import urljoin

# Load service URLs from env (or default to Docker hostnames)
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "user": os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
    "flights": os.getenv("FLIGHTS_SERVICE_URL", "http://flights-service:8000"),
    "ferries": os.getenv("FERRIES_SERVICE_URL", "http://ferries-service:8000"),
    "hotels": os.getenv("HOTELS_SERVICE_URL", "http://hotels-service:8000"),
    "ppob": os.getenv("PPOB_SERVICE_URL", "http://ppob-service:8000"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000"),
    "transaction": os.getenv("TRANSACTION_SERVICE_URL", "http://transaction-service:8000"),
    "trains": os.getenv("TRAINS_SERVICE_URL", "http://trains-service:8000"),
}

# Map prefixes to service keys
ROUTE_SERVICE_MAP = {
    "api/v1/flights": "flights",
    "api/v1/bookings": "flights",
    "api/v1/ferries": "ferries",
    "hotels": "hotels",
    "ppob": "ppob",
    "payments": "payment",
    "transactions": "transaction",
    "trains": "trains",
}

def resolve_target_url(path: str) -> str | None:
    for prefix, service_key in ROUTE_SERVICE_MAP.items():
        if path.startswith(prefix):
            return urljoin(SERVICES[service_key] + "/", path)
    return None

async def forward_request(request: Request, full_path: str) -> Response:
    """
    Forwards a request from API Gateway to the target microservice.
    """
    target_url = resolve_target_url(full_path)
    
    if not target_url:
        print(f"❌ No route matched for path: /{full_path}")
        return Response(content="Service not found", status_code=404)

    print(f"📦 FORWARDING {request.method} → {target_url}")

    # Get request body
    body = await request.body()

    # Get headers (excluding host and content-length)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body if request.method.upper() != "GET" else None,
                timeout=30
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.RequestError as e:
            print(f"❌ Request failed: {e}")
            return Response(
                content=f"Service unavailable: {str(e)}",
                status_code=503
            )

