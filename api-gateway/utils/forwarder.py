import os
import httpx

from fastapi import Request, Response

# Load service URLs from env
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000"),
    "user": os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
    "flights": os.getenv("FLIGHTS_SERVICE_URL", "http://flights-service:8000"),
    "ferries": os.getenv("FERRIES_SERVICE_URL", "http://ferries-service:8000"),
    "hotels": os.getenv("HOTELS_SERVICE_URL", "http://hotels-service:8000"),
    "ppob": os.getenv("PPOB_SERVICE_URL", "http://ppob-service:8000"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000"),
}

ROUTE_SERVICE_MAP = {
    "/auth": "auth",
    "/users": "user",
    "/flights": "flights",
    "/ferries": "ferries",
    "/hotels": "hotels",
    "/ppob": "ppob",
    "/payments": "payment",
}


def resolve_target_url(path: str) -> str | None:
    """
    Match the route to a service and build the full URL.
    """
    for prefix, service in ROUTE_SERVICE_MAP.items():
        if path.startswith(prefix.lstrip("/")):
            return f"{SERVICES[service]}/{path}"
    return None


async def forward_request(request: Request, full_path: str) -> Response:
    """
    Forward the request to the matched service.
    """
    target_url = resolve_target_url(full_path)
    if not target_url_
