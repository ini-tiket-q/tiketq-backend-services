from sqlalchemy import Column, Index, Integer, String, ForeignKey, DateTime, DECIMAL, Enum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from domain.base import Base
from shared.chrono import utc_now

class Passenger(Base):
    __tablename__ = "passengers"
    __table_args__ = (
        Index("idx_passenger_name", "full_name"),
        Index("idx_passenger_id_number", "id_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    id_number: Mapped[str] = mapped_column(String, nullable=False)
    nationality: Mapped[str] = mapped_column(String, nullable=False)
    seat_number: Mapped[str] = mapped_column(String, nullable=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="passengers")

    def __repr__(self):
        return f"<Passenger id={self.id} name={self.full_name} seat={self.seat_number}>"

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("idx_booking_status", "status"),
        Index("idx_booking_departure", "departure_datetime"),
        Index("idx_booking_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False)
    return_trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True)
    passenger_count: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_provider: Mapped[str] = mapped_column(String, nullable=False)
    payment_reference: Mapped[str] = mapped_column(String, nullable=False)
    gateway_transaction_id: Mapped[str] = mapped_column(String, nullable=False)
    refund_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    agent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utc_now, onupdate=datetime.utc_now)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="bookings")
    passengers: Mapped[list["Passenger"]] = relationship("Passenger", back_populates="booking")
    
    def __repr__(self):
        return f"<Booking id={self.id} user={self.user_id} status={self.status} passengers={self.passenger_count}>"