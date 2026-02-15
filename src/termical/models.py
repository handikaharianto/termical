"""Database models for termical."""
from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Activity(Base):
    """Activity model representing a calendar event."""
    
    __tablename__ = "activities"
    
    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attendees: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, 
        nullable=False, 
        server_default='[]'
    )
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, 
        nullable=False, 
        server_default='[]'
    )
    last_synced: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"Activity(event_id={self.event_id!r}, title={self.title!r}, start_time={self.start_time!r})"
