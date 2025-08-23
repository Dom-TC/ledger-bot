"""The EventMember model."""

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .base import Base
from .event import Event
from .member import Member


class MemberStatus(enum.Enum):
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
    has_paid: Mapped[bool] = mapped_column(
        Integer, default=0
    )  # SQLite uses INT for bool
    status: Mapped[MemberStatus] = mapped_column(
        Enum(MemberStatus), nullable=False, default=MemberStatus.CONFIRMED
    )
    joined_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="members")
    member: Mapped["Member"] = relationship("Member")
