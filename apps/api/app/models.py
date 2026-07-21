import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    order_quantity_kg: Mapped[float] = mapped_column(Float)
    available_batch_sizes_kg: Mapped[list] = mapped_column(JSON, default=list)
    minimum_batch_size_kg: Mapped[float] = mapped_column(Float)
    maximum_batch_size_kg: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="draft")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    suggestions: Mapped[list["Suggestion"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    decisions: Mapped[list["UserDecision"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    batches: Mapped[list] = mapped_column(JSON)
    score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(String)
    explanation_polished: Mapped[str | None] = mapped_column(String, nullable=True)
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    historically_preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="suggestions")


class UserDecision(Base):
    __tablename__ = "user_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    suggestion_id: Mapped[str] = mapped_column(ForeignKey("suggestions.id"))
    final_batches: Mapped[list] = mapped_column(JSON)
    accepted_without_changes: Mapped[bool] = mapped_column(Boolean)
    change_count: Mapped[int] = mapped_column(Integer)
    change_types: Mapped[list] = mapped_column(JSON, default=list)
    change_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    similarity_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="decisions")
    suggestion: Mapped["Suggestion"] = relationship()
