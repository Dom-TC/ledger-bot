"""The event model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event_member import EventMember
    from .event_wine import EventWine
    from .member import Member


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    event_description: Mapped[Optional[str]] = mapped_column(Text)
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    event_location: Mapped[Optional[str]] = mapped_column(String)
    host_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    max_guests: Mapped[Optional[int]] = mapped_column(
        Integer,
    )
    deposit_value: Mapped[Optional[int]] = mapped_column(Integer)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    channel_id: Mapped[Optional[int]] = mapped_column(Integer)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    members: Mapped[List["EventMember"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    wines: Mapped[List["EventWine"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    host: Mapped["Member"] = relationship(back_populates="hosted_events")
