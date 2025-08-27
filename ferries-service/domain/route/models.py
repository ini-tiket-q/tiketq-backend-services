from typing import List, Optional
from sqlalchemy import Integer, String, Boolean, Float, ForeignKey, Index, DECIMAL, DateTime, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from domain.base import Base
from datetime import datetime

class Port(Base):
    __tablename__ = "ports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    routes_from: Mapped[List["Route"]] = relationship("Route", back_populates="origin", foreign_keys="Route.origin_id")
    routes_to: Mapped[List["Route"]] = relationship("Route", back_populates="destination", foreign_keys="Route.destination_id")

    def __repr__(self) -> str:
        return f"<Port(id={self.id}, code={self.code}, city={self.city}, country={self.country})>"


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (
        Index("idx_route_origin_dest", "origin_id", "destination_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    origin_id: Mapped[int] = mapped_column(ForeignKey("ports.id"), nullable=False)
    destination_id: Mapped[int] = mapped_column(ForeignKey("ports.id"), nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Float)
    duration_est: Mapped[int | None] = mapped_column(Integer)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)

    origin: Mapped["Port"] = relationship("Port", foreign_keys=[origin_id], back_populates="routes_from")
    destination: Mapped["Port"] = relationship("Port", foreign_keys=[destination_id], back_populates="routes_to")
    sectors: Mapped[list["Sector"]] = relationship("Sector", back_populates="primary_route")
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="route")


class Sector(Base):
    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    primary_route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False)
    next_sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"), nullable=True)
    is_roundtrip: Mapped[bool] = mapped_column(Boolean, default=False)

    primary_route: Mapped["Route"] = relationship("Route", back_populates="sectors")
    next_sector: Mapped["Sector"] = relationship("Sector", remote_side=[id])
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="sector")
    
    def __repr__(self) -> str:
        return f"<Sector(id={self.id}, name={self.name}, primary_route={self.primary_route_id}, roundtrip={self.is_roundtrip})>"
    
class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        Index("idx_trip_status", "status"),
        Index("idx_trip_departure", "departure_datetime"),
        Index("idx_trip_route", "route_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False)
    ferry_id: Mapped[int] = mapped_column(ForeignKey("ferries.id"), nullable=False)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectors.id"), nullable=False)
    ferry_class_id: Mapped[int] = mapped_column(ForeignKey("ferry_classes.id"), nullable=False)
    departure_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    arrival_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    price_override: Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    status: Mapped[str] = mapped_column(String, default="SCHEDULED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utc_now, onupdate=datetime.utc_now)
    metadata: Mapped[dict | None] = mapped_column(JSON)

    route = relationship("Route", back_populates="trips")
    ferry = relationship("Ferry", back_populates="trips")
    sector = relationship("Sector", back_populates="trips")
    ferry_class = relationship("FerryClass", back_populates="trips")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="trip")


def __repr__(self) -> str:
        return (
            f"<Trip(id={self.id}, route={self.route_id}, ferry={self.ferry_id}, "
            f"departure={self.departure_datetime}, status={self.status})>"
        )