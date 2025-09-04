from adapters.sindo_api_calls import SindoClient
from utils.date_formatter import format_date_for_sindo

sindo_client = SindoClient() 


def get_routes_dashboard(search: str = None):
    raw_data = sindo_client.get_sindo_routes(search)

    # fallback kalau gagal atau response tidak sesuai
    if not raw_data or raw_data.get("status") != "Ok":
        return {"status": "error", "data": []}

    records = raw_data.get("data", {}).get("records", [])
    routes = []
    for item in records:
        routes.append({
            "route_id": item.get("id"),
            "code": item.get("code"),
            "name": item.get("name"),
            "origin": {
                "id": item.get("embarkationPort", {}).get("id"),
                "code": item.get("embarkationPort", {}).get("code"),
                "name": item.get("embarkationPort", {}).get("name"),
            },
            "destination": {
                "id": item.get("destinationPort", {}).get("id"),
                "code": item.get("destinationPort", {}).get("code"),
                "name": item.get("destinationPort", {}).get("name"),
            },
            "sector": {
                "id": item.get("sector", {}).get("id"),
                "code": item.get("sector", {}).get("code"),
                "name": item.get("sector", {}).get("name"),
            }
        })

    return {
        "status": "success",
        "total": raw_data.get("data", {}).get("totalRecords", len(routes)),
        "data": routes
    }

#oneway
def get_trips_dashboard(
    origin: str, 
    destination: str, 
    date: str,
    pax: int, 
    ferry_class: str
):
    sindo_date = format_date_for_sindo(date)
    
    raw_data = sindo_client.get_sindo_trips(
        origin, destination, sindo_date
    )
    trips = []
    for item in raw_data:  # list response
        trips.append({
            "trip_id": item.get("tripID"),
            "departure_time": item.get("departureTime"),
            "arrival_time": item.get("arrivalTime"),
            "status": item.get("status"),
            "available_seats": item.get("usedSeat"),  
            "gate_open": item.get("gateOpen"),
            "gate_close": item.get("gateClose"),
            "route": f"{origin}-{destination}",  # Added route info
            "pax": pax,  # Include passenger count in response
            "ferry_class": ferry_class,
        })
    return {"status": "success", "data": trips}

#roundtrip
def get_roundtrip_dashboard(
    origin: str, 
    destination: str, 
    depart_date: str, 
    return_date: str, 
    pax: int,
    ferry_class: str
):
    sindo_depart_date = format_date_for_sindo(depart_date)
    sindo_return_date = format_date_for_sindo(return_date)
    
    raw_data = sindo_client.get_sindo_roundtrip(
        origin, destination, sindo_depart_date, sindo_return_date, pax
    )
    # Normalize here -adjust based on actual response structure
    normalized = []
    for item in raw_data:
        normalized.append({
            "route": f"{origin}-{destination}",
            "departure_time": item.get("departureTime"),
            "return_time": item.get("returnTime"),
            "status": item.get("status"),
            "available_seats": item.get("usedSeat"),
            "pax": pax,  # Include passenger count in response
            "ferry_class": ferry_class,
            # Add other necessary fields
        })
    return {"status": "success", "data": normalized}