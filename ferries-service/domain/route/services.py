from adapters.sindo_ferry_api import sindo_client
from domain.route.schemas import TripSearchRequest, TripSearchResponse, TripOption


def get_routes_service(search: str = None):
    raw = sindo_client.get_routes(search)
    # normalisasi → FE tidak langsung tergantung raw dari Sindo
    routes = [
        {
            "id": r.get("id"),
            "origin": r.get("originPortCode"),
            "destination": r.get("destinationPortCode"),
            "duration": r.get("duration"),
        }
        for r in raw.get("data", [])
    ]
    return {"status": "success", "data": routes}
















# client = SindoClient()

# def search_trips(req: TripSearchRequest) -> TripSearchResponse:
#     params = {
#         "origin": req.origin,
#         "destination": req.destination,
#         "departure_date": req.departure_date
#     }
#     if req.return_date:
#         params["return_date"] = req.return_date

#     raw_data = client.search_trips(params)

#     trips = [
#         TripOption(
#             id=trip["id"],
#             origin=trip["origin"],
#             destination=trip["destination"],
#             departure_time=trip["departure_time"],
#             arrival_time=trip["arrival_time"],
#             price=float(trip["price"])
#         )
#         for trip in raw_data.get("trips", [])
#     ]
#     return TripSearchResponse(trips=trips)
