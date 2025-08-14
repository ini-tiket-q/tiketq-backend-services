from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from domain.services import TrainStationService, TrainSearchService
from adapters.external_api import StaticTrainStationAdapter, MockKAIAccessAPIAdapter
from pydantic import BaseModel
import logging

# Initialize adapters
station_adapter = StaticTrainStationAdapter()

# Initialize services
station_service = TrainStationService(station_adapter)

# Add after existing imports
external_api = MockKAIAccessAPIAdapter()
search_service = TrainSearchService(external_api, station_adapter)

router = APIRouter()

@router.get("/stations")
async def get_stations(search: Optional[str] = Query(None)):
    """Get all train stations or search by query"""
    try:
        if search:
            stations = station_service.search_stations(search)
        else:
            stations = station_service.get_all_stations()
        
        return {
            'stations': [
                {
                    'code': station.code,
                    'name': station.name,
                    'city': station.city,
                    'province': station.province
                }
                for station in stations
            ]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error getting stations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Pydantic models
class TrainSearchRequestModel(BaseModel):
    origin_code: str
    destination_code: str
    departure_date: str
    adult_count: int = 1
    infant_count: int = 0

@router.post("/search")
async def search_trains(request: TrainSearchRequestModel):
    """Search for available trains"""
    try:
        from domain.models import TrainSearchRequest
        # Create search request
        search_request = TrainSearchRequest(
            origin_code=request.origin_code,
            destination_code=request.destination_code,
            departure_date=request.departure_date,
            adult_count=request.adult_count,
            infant_count=request.infant_count
        )
        # Gunakan service untuk pencarian kereta
        schedules = search_service.search_trains(search_request)
        return {
            'origin': request.origin_code,
            'destination': request.destination_code,
            'schedules': [
                {
                    'train_number': s.train_number,
                    'train_name': s.train_name,
                    'departure_station': s.departure_station.name,
                    'arrival_station': s.arrival_station.name,
                    'departure_time': str(s.departure_time),
                    'arrival_time': str(s.arrival_time),
                    'duration': s.duration,
                    'classes': [
                        {
                            'class_name': c.class_name,
                            'subclass': c.subclass,
                            'fare': c.fare,
                            'available_seats': c.available_seats
                        } for c in s.classes
                    ],
                    'date': s.date
                } for s in schedules
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error searching trains: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")