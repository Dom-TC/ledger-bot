"""The event model."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .event_member import EventMember
from .event_wine import EventWine


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    event_description: Mapped[Optional[str]] = mapped_column(Text)
    event_date: Mapped[datetime] = mapped_column(DateTime)
    event_location: Mapped[Optional[str]] = mapped_column(String)
    event_host: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    deposit_value: Mapped[Optional[int]] = mapped_column(Integer)
    creation_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    channel_id: Mapped[Optional[str]] = mapped_column(String)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    members: Mapped[List["EventMember"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    wines: Mapped[List["EventWine"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
