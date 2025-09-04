from adapters.sindo_api_calls import SindoClient


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


def get_trips_dashboard(origin: str, destination: str, date: str):
    raw_data = sindo_client.get_trips(origin, destination, date)
    trips = []
    for item in raw_data.get("data", []):  # cek sesuai response Sindo
        trips.append({
            "embarkation": item.get("embarkation"),
            "destination": item.get("destination"),
            "depart_time": item.get("departureTime"),
            "arrival_time": item.get("arrivalTime"),
            "price": item.get("price"),
        })
    return {"status": "success", "data": trips}


def get_roundtrip_dashboard(params: dict):
    api_params = {
        "embarkation": params["origin"],
        "destination": params["destination"],
        "departdate": params["depart_date"],   # sesuai dokumen Sindo
        "returndate": params["return_date"]
    }
    raw_data = sindo_client.get_sindo_roundtrip(api_params)
    # Normalisasi / transform data
    normalized = []
    for item in raw_data.get("trips", []):
        normalized.append({
            "route": item.get("routeName"),
            "depart_time": item.get("departureTime"),
            "return_time": item.get("returnTime"),
            "price": item.get("price"),
        })
    return {"status": "success", "data": normalized}