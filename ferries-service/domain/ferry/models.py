from typing import List
from sqlalchemy import DECIMAL,Index, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from domain.base import Base



class Ferry(Base):
    __tablename__ = "ferries"
    __table_args__ = (
        Index("idx_ferry_name", "ferry_name"),
        Index("idx_operator_name", "operator_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ferry_name: Mapped[str] = mapped_column(String, nullable=False)
    ferry_number: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    operator_name: Mapped[str] = mapped_column(String, nullable=False)

    classes: Mapped[List["FerryClass"]] = relationship("FerryClass", back_populates="ferry")
    trips: Mapped[List["Trip"]] = relationship("Trip", back_populates="ferry")

    def __repr__(self):
        return f"<Ferry id={self.id} name='{self.name}' number={self.ferry_number} capacity={self.capacity}>"
    
    
class FerryClass(Base):
    __tablename__ = "ferry_classes"
    __table_args__ = (
        Index("idx_ferry_class_name", "class_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ferry_id: Mapped[int] = mapped_column(ForeignKey("ferries.id"), nullable=True)
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    seat_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_base: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)

    ferry: Mapped["Ferry"] = relationship("Ferry", back_populates="classes", lazy="joined") #optional
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="ferry_class")
    
    def __repr__(self):
        return f"<FerryClass id={self.id} class='{self.class_name}' seats={self.seat_capacity} price={self.price_base}>"