"""The EventMember model."""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event
    from .event_wine import EventWine
    from .member import Member


class EventMemberStatus(enum.Enum):
    HOST = "host"
    CONFIRMED = "confirmed"
    WAITLIST = "waitlist"
    CANCELLED = "cancelled"


class EventMember(Base):
    __tablename__ = "event_members"
    __table_args__ = (
        UniqueConstraint("event_id", "member_id", name="uq_event_member"),
    )

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    guests: Mapped[int] = mapped_column(Integer, default=0)
    has_paid: Mapped[bool] = mapped_column(Integer, default=0)
    status: Mapped[EventMemberStatus] = mapped_column(
        Enum(EventMemberStatus), nullable=False, default=EventMemberStatus.CONFIRMED
    )
    joined_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    paid_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    event: Mapped["Event"] = relationship(
        "Event", back_populates="members", lazy="joined"
    )
    member: Mapped["Member"] = relationship(
        "Member", back_populates="attending_events", lazy="joined"
    )
    wines: Mapped[List["EventWine"]] = relationship(
        "EventWine", back_populates="event_member", cascade="all, delete-orphan"
    )
