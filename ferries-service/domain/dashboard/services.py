from requests import RequestException
from adapters.sindo_api_calls import SindoClient
from utils.date_formatter import format_date_for_sindo
from utils.error_handling import SindoAPIError
import logging

sindo_client = SindoClient() 

logger = logging.getLogger(__name__)

def get_routes_dashboard(search: str = None):
        try:
            raw_data = sindo_client.get_sindo_routes(search)
            logger.info(f"Raw response from Sindo routes API: {raw_data}")
            # fallback kalau gagal atau response tidak sesuai
            if not raw_data or raw_data.get("status") != "Ok":
                logger.error(f"Sindo routes API returned error or empty response: {raw_data}")
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
                "data": routes,
                "raw_data": raw_data  # for debugging
            }
        except RequestException as e:
            logger.error(f"RequestException in get_routes_dashboard: {str(e)}")
            raise SindoAPIError(f"Failed to fetch routes from Sindo API: {str(e)}")
        except Exception as e:
            # Handle any other unexpected errors
            logger.error(f"Unexpected error in get_routes_dashboard: {str(e)}")
            raise SindoAPIError(f"Unexpected error while processing routes: {str(e)}")


    #oneway
def get_trips_dashboard(
        origin: str, 
        destination: str, 
        date: str,
        pax: int =1, 
        ferry_class: str = "economy"
    ):
        try:
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
        except RequestException as e:
            raise SindoAPIError(f"Failed to fetch trips from Sindo API: {str(e)}")
        except Exception as e:
        # Handle any other unexpected errors
            raise SindoAPIError(f"Unexpected error while processing trips: {str(e)}")


    #roundtrip
def get_roundtrip_dashboard(
        origin: str, 
        destination: str, 
        depart_date: str, 
        return_date: str, 
        pax: int =1, 
        ferry_class: str = "economy"
    ):
        try:
            # Get departure trips (origin → destination)
            depart_trips = get_trips_dashboard(origin, destination, depart_date, pax, ferry_class)
            
            # Get return trips (destination → origin) 
            return_trips = get_trips_dashboard(destination, origin, return_date, pax, ferry_class)
            
            # Check if either request failed
            if depart_trips.get("status") == "error":
                return depart_trips
            if return_trips.get("status") == "error":
                return return_trips
            
            # Combine the results
            return {
                "status": "success",
                "data": {
                    "departure_trips": depart_trips.get("data", []),
                    "return_trips": return_trips.get("data", [])
                }
            }
        except Exception as e:
        # Handle any unexpected errors
            raise SindoAPIError(f"Unexpected error while processing roundtrip: {str(e)}")    