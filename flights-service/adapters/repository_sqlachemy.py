import os, uuid, json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".." / ".env")


from datetime import datetime, date
from typing import Iterable, Optional, List, Tuple
from sqlalchemy import create_engine, select, and_, func, String, DateTime, Text, UniqueConstraint, Integer, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session, relationship
from math import ceil

# ⬇️ ABSOLUTE imports from within app dir (no hyphen!)
from domain.models import Flight, Booking, Passenger, Payment
from domain.repository import FlightRepository, BookingRepository

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

class BookingModel(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(100))
    contact_phone: Mapped[str] = mapped_column(String(32))
    contact_email: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(16), index=True)

    route_from: Mapped[str] = mapped_column(String(3), index=True)
    route_to: Mapped[str]   = mapped_column(String(3), index=True)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True)
    arrival_time:   Mapped[datetime] = mapped_column(DateTime(timezone=False))

    flight_number: Mapped[str] = mapped_column(String(16))
    airline: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cabin:   Mapped[str | None] = mapped_column(String(16), nullable=True)

    pax_adult:  Mapped[int] = mapped_column(Integer, default=1)
    pax_child:  Mapped[int] = mapped_column(Integer, default=0)
    pax_infant: Mapped[int] = mapped_column(Integer, default=0)

    fare_amount:   Mapped[int] = mapped_column(Integer)
    fare_currency: Mapped[str] = mapped_column(String(8))

    offer_id: Mapped[str] = mapped_column(String(128))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

    passengers: Mapped[list["PassengerModel"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    payment: Mapped["PaymentModel"] = relationship(back_populates="booking", uselist=False)

class PassengerModel(Base):
    __tablename__ = "booking_passengers"
    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(12))
    full_name: Mapped[str] = mapped_column(String(100))
    dob: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    id_no: Mapped[str | None] = mapped_column(String(64), nullable=True)

    booking: Mapped["BookingModel"] = relationship(back_populates="passengers")

class PaymentModel(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), index=True, unique=True)
    provider: Mapped[str] = mapped_column(String(32))
    status:   Mapped[str] = mapped_column(String(16), index=True)
    amount:   Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8))
    snap_token:  Mapped[str | None] = mapped_column(String(128), nullable=True)
    redirect_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_provider_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)

    booking: Mapped["BookingModel"] = relationship(back_populates="payment")

def _to_booking_domain(m: BookingModel) -> Booking:
    return Booking(
        id=m.id, user_id=m.user_id, contact_name=m.contact_name, contact_phone=m.contact_phone, contact_email=m.contact_email,
        status=m.status, route_from=m.route_from, route_to=m.route_to, departure_time=m.departure_time, arrival_time=m.arrival_time,
        flight_number=m.flight_number, airline=m.airline, cabin=m.cabin, pax_adult=m.pax_adult, pax_child=m.pax_child, pax_infant=m.pax_infant,
        fare_amount=m.fare_amount, fare_currency=m.fare_currency, offer_id=m.offer_id, created_at=m.created_at, updated_at=m.updated_at
    )

def _to_payment_domain(m: PaymentModel) -> Payment:
    return Payment(
        id=m.id, booking_id=m.booking_id, provider=m.provider, status=m.status, amount=m.amount, currency=m.currency,
        snap_token=m.snap_token, redirect_url=m.redirect_url, raw_provider_payload=m.raw_provider_payload,
        created_at=m.created_at, updated_at=m.updated_at
    )

class SqlAlchemyBookingRepo(BookingRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_booking(self, booking: Booking, passengers: list[Passenger]) -> Booking:
        bid = uuid.uuid4().hex[:26]
        bm = BookingModel(
            id=bid,
            user_id=booking.user_id,
            contact_name=booking.contact_name, contact_phone=booking.contact_phone, contact_email=booking.contact_email,
            status=booking.status,
            route_from=booking.route_from, route_to=booking.route_to,
            departure_time=booking.departure_time, arrival_time=booking.arrival_time,
            flight_number=booking.flight_number, airline=booking.airline, cabin=booking.cabin,
            pax_adult=booking.pax_adult, pax_child=booking.pax_child, pax_infant=booking.pax_infant,
            fare_amount=booking.fare_amount, fare_currency=booking.fare_currency,
            offer_id=booking.offer_id,
        )
        for p in passengers:
            pm = PassengerModel(
                id=uuid.uuid4().hex[:26],
                booking_id=bid,
                type=p.type,
                full_name=p.full_name,
                dob=p.dob,
                id_no=p.id_no
            )
            bm.passengers.append(pm)
        self.session.add(bm)
        self.session.commit()
        self.session.refresh(bm)
        return _to_booking_domain(bm)

    def get_booking(self, booking_id: str) -> Booking:
        m = self.session.get(BookingModel, booking_id)
        if not m:
            raise KeyError("Booking not found")
        return _to_booking_domain(m)
    
    def get_booking_by_id(self, booking_id: str) -> Booking | None:
        m = self.session.get(BookingModel, booking_id)
        return _to_booking_domain(m) if m else None


    def list_bookings(self, *, user_id=None, email=None, phone=None, page=1, per_page=10) -> tuple[list[Booking], int]:
        stmt = select(BookingModel)
        if user_id:
            stmt = stmt.where(BookingModel.user_id == user_id)
        elif email and phone:
            stmt = stmt.where(and_(BookingModel.contact_email == email, BookingModel.contact_phone == phone))
        # total
        total = self.session.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        # paging
        stmt = stmt.order_by(BookingModel.created_at.desc()).offset((page-1)*per_page).limit(per_page)
        rows = self.session.execute(stmt).scalars().all()
        return [_to_booking_domain(m) for m in rows], total

    def create_payment_for_booking(self, booking_id: str, amount: int, currency: str):
    # 1) If a payment already exists for this booking, just return it (idempotent)
        existing = self.session.execute(
            select(PaymentModel).where(PaymentModel.booking_id == booking_id)
        ).scalar_one_or_none()
        if existing is not None:
            return _to_payment_domain(existing)

        # 2) Otherwise create it
        m = PaymentModel(
            id=uuid.uuid4().hex[:26],
            booking_id=booking_id,
            provider="MIDTRANS",
            status="PENDING",
            amount=amount,
            currency=currency,
            snap_token=None,
            redirect_url=None,
            raw_provider_payload=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(m)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            # another request raced us; fetch and return
            raced = self.session.execute(
                select(PaymentModel).where(PaymentModel.booking_id == booking_id)
            ).scalar_one_or_none()
            if raced is None:
                # unexpected, but bubble up
                raise
            return _to_payment_domain(raced)

        return _to_payment_domain(m)

    def get_payment_by_booking(self, booking_id: str) -> Payment | None:
        stmt = select(PaymentModel).where(PaymentModel.booking_id == booking_id)
        m = self.session.execute(stmt).scalar_one_or_none()
        return _to_payment_domain(m) if m else None

    def mark_payment_paid(self, payment_id: str, *, raw_payload: dict | None = None) -> Payment:
        m = self.session.get(PaymentModel, payment_id)
        if not m:
            raise KeyError("Payment not found")

        m.status = "PAID"
        if raw_payload is not None:
            # 👇 serialize dict to JSON string
            m.raw_provider_payload = json.dumps(raw_payload)

        m.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(m)
        return _to_payment_domain(m)

    def confirm_booking(self, booking_id: str):
        obj = self.session.get(BookingModel, booking_id)
        if not obj:
            raise KeyError("Booking not found")
        obj.status = "CONFIRMED"
        obj.updated_at = datetime.utcnow()
        self.session.commit()
        return obj