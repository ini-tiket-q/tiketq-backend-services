import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List, Optional
from domain.models import TrainSchedule, TrainStation, TrainClass
import json
from sqlalchemy import Time

# 1. Koneksi DB
DATABASE_URL = os.getenv("TRAINS_DB_URL", "sqlite:///trains.db")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TrainScheduleTable(Base):
    __tablename__ = "train_schedules"
    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String)
    train_name = Column(String)
    departure_station = Column(String)
    arrival_station = Column(String)
    departure_time = Column(Time)
    arrival_time = Column(Time)
    duration = Column(String)
    classes = Column(String)
    date = Column(String)


class DBTrainRepository:
    def _to_domain(self, db_schedule: TrainScheduleTable) -> TrainSchedule:
        # decode JSON string ke object
        departure_station = TrainStation(**json.loads(db_schedule.departure_station))
        arrival_station = TrainStation(**json.loads(db_schedule.arrival_station))
        classes = [TrainClass(**c) for c in json.loads(db_schedule.classes)]

        return TrainSchedule(
            id=db_schedule.id,
            train_number=db_schedule.train_number,
            train_name=db_schedule.train_name,
            departure_station=departure_station,
            arrival_station=arrival_station,
            departure_time=db_schedule.departure_time,
            arrival_time=db_schedule.arrival_time,
            duration=db_schedule.duration,
            classes=classes,
            date=db_schedule.date,
        )

    def get_by_id(self, schedule_id: int) -> Optional[TrainSchedule]:
        with SessionLocal() as db:
            db_schedule = db.query(TrainScheduleTable).filter(TrainScheduleTable.id == schedule_id).first()
            if db_schedule:
                return self._to_domain(db_schedule)
            return None

    def get_all(self) -> List[TrainSchedule]:
        with SessionLocal() as db:
            all_db_schedules = db.query(TrainScheduleTable).all()
            return [self._to_domain(schedule) for schedule in all_db_schedules]

    def create_schedule(self, schedule: TrainSchedule) -> TrainSchedule:
        with SessionLocal() as db:
            db_schedule = TrainScheduleTable(
                train_number=schedule.train_number,
                train_name=schedule.train_name,
                departure_station=json.dumps(schedule.departure_station.__dict__),
                arrival_station=json.dumps(schedule.arrival_station.__dict__),
                departure_time=schedule.departure_time,
                arrival_time=schedule.arrival_time,
                duration=schedule.duration,
                classes=json.dumps([cls.__dict__ for cls in schedule.classes]),
                date=schedule.date
            )
            db.add(db_schedule)
            db.commit()
            db.refresh(db_schedule)
            return self._to_domain(db_schedule)