import os, uuid
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".." / ".env")


from datetime import datetime, date
from typing import Iterable, Optional, List, Tuple
from sqlalchemy import create_engine, select, and_, func, String, DateTime, Text, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from math import ceil

# ⬇️ ABSOLUTE imports from within app dir (no hyphen!)
from domain.models import Flight
from domain.repository import FlightRepository

DB_URL = os.getenv("FLIGHTS_DB_URL", "sqlite:///./flight.db")
engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase): pass

class FlightModel(Base):
    __tablename__ = "flights"
    __table_args__ = (
        UniqueConstraint("flight_number", "departure_time", name="uq_flight_departure"),
    )

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    flight_number: Mapped[str] = mapped_column(String(10), index=True)
    from_airport: Mapped[str] = mapped_column(String(3), index=True)
    to_airport: Mapped[str] = mapped_column(String(3), index=True)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    aircraft_type: Mapped[str] = mapped_column(String(20))
    gate: Mapped[str | None] = mapped_column(String(10), nullable=True)
    terminal: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="SCHEDULED")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)  # 👈


def to_domain(m: FlightModel) -> Flight:
    return Flight(
        id=m.id, flight_number=m.flight_number,
        from_airport=m.from_airport, to_airport=m.to_airport,
        departure_time=m.departure_time, arrival_time=m.arrival_time,
        aircraft_type=m.aircraft_type, gate=m.gate, terminal=m.terminal,
        status=m.status, notes=m.notes
    )

class SqlAlchemyFlightRepo(FlightRepository):
    def __init__(self, session: Session): self.session = session
    
    def list(self, *, frm: Optional[str]=None, to: Optional[str]=None, day: Optional[date]=None):
        stmt = select(FlightModel).where(FlightModel.deleted_at.is_(None))
        conds = []
        if frm: conds.append(FlightModel.from_airport == frm.upper())
        if to:  conds.append(FlightModel.to_airport == to.upper())
        if day: conds.append(func.date(FlightModel.departure_time) == day.isoformat())
        if conds: stmt = stmt.where(and_(*conds))
        stmt = stmt.order_by(FlightModel.departure_time.asc())
        rows = self.session.execute(stmt).scalars().all()
        return [to_domain(m) for m in rows]
    
    def get(self, flight_id: str) -> Flight:
        m = self.session.get(FlightModel, flight_id)
        if not m or m.deleted_at is not None:     # 👈
            raise KeyError("Flight not found")
        return to_domain(m)
    
    def create(self, flight: Flight) -> Flight:
        dup = self.session.execute(
            select(FlightModel).where(
                (FlightModel.flight_number == flight.flight_number) &
                (FlightModel.departure_time == flight.departure_time)
            )
        ).scalar_one_or_none()
        if dup: raise ValueError("Duplicate flight for number+departure_time")
        m = FlightModel(
            id=uuid.uuid4().hex[:26],
            flight_number=flight.flight_number,
            from_airport=flight.from_airport.upper(),
            to_airport=flight.to_airport.upper(),
            departure_time=flight.departure_time,
            arrival_time=flight.arrival_time,
            aircraft_type=flight.aircraft_type,
            gate=flight.gate, terminal=flight.terminal,
            status=flight.status, notes=flight.notes
        )
        self.session.add(m); self.session.commit(); self.session.refresh(m)
        return to_domain(m)
    
    def update(self, flight_id: str, **fields) -> Flight:
        m = self.session.get(FlightModel, flight_id)
        if not m or m.deleted_at is not None:
            raise KeyError("Flight not found")

        # Optional: simple business rule if both times present
        dep = fields.get("departure_time", m.departure_time)
        arr = fields.get("arrival_time", m.arrival_time)
        if dep and arr and arr <= dep:
            raise ValueError("arrival_time must be after departure_time")

        # Normalize IATA if provided
        if "from_airport" in fields and fields["from_airport"]:
            fields["from_airport"] = fields["from_airport"].upper()
        if "to_airport" in fields and fields["to_airport"]:
            fields["to_airport"] = fields["to_airport"].upper()

        # Apply fields
        for k, v in fields.items():
            setattr(m, k, v)

        try:
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            # likely unique (flight_number, departure_time)
            raise ValueError("Duplicate flight for number+departure_time") from e

        self.session.refresh(m)
        return to_domain(m)

    def soft_delete(self, flight_id: str) -> None:
        m = self.session.get(FlightModel, flight_id)
        if not m or m.deleted_at is not None:
            raise KeyError("Flight not found")
        m.deleted_at = datetime.utcnow()
        self.session.commit()

    def list_paginated(
        self,
        *,
        frm: Optional[str] = None,
        to: Optional[str] = None,
        day: Optional[date] = None,
        page: int = 1,
        per_page: int = 10,
        sort: Optional[str] = None,
    ) -> Tuple[List[Flight], int]:
        # base filter
        conds = [FlightModel.deleted_at.is_(None)]
        if frm: conds.append(FlightModel.from_airport == frm.upper())
        if to:  conds.append(FlightModel.to_airport == to.upper())
        if day: conds.append(func.date(FlightModel.departure_time) == day.isoformat())

        # total count
        # (use subquery for correct count with same filters)
        from sqlalchemy import select
        base_q = select(FlightModel.id).where(and_(*conds))
        total = self.session.execute(
            select(func.count()).select_from(base_q.subquery())
        ).scalar_one()

        # sorting
        sort_map = {
            "departure_time": FlightModel.departure_time,
            "arrival_time": FlightModel.arrival_time,
            "flight_number":   FlightModel.flight_number,
            "from_airport":    FlightModel.from_airport,
            "to_airport":      FlightModel.to_airport,
            "status":          FlightModel.status,
        }
        order_by = []
        if sort:
            for token in sort.split(","):
                token = token.strip()
                if not token: 
                    continue
                direction = "asc"
                field = token
                if token[0] in "+-":
                    direction = "desc" if token[0] == "-" else "asc"
                    field = token[1:]
                col = sort_map.get(field)
                if col is not None:
                    order_by.append(col.desc() if direction == "desc" else col.asc())
        if not order_by:
            order_by = [FlightModel.departure_time.asc()]  # default

        # pagination
        page = max(1, int(page))
        per_page = min(max(1, int(per_page)), 100)   
        offset = (page - 1) 
        stmt = (
            select(FlightModel)
            .where(and_(*conds))
            .order_by(*order_by)
            .limit(per_page)
            .offset(offset)
        )
        rows = self.session.execute(stmt).scalars().all()
        return [to_domain(m) for m in rows], total

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()
