"""The event model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Integer, String, Text, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from .base import Base
from .event_member import EventMember, MemberStatus
from .event_wine import EventWine

if TYPE_CHECKING:
    from .bot_message import BotMessage


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    event_name: Mapped[str] = mapped_column(String, nullable=False)
    event_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    event_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    max_guests: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deposit_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    channel_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    members: Mapped[List["EventMember"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", lazy="joined"
    )
    waitlisted_members: Mapped[List["EventMember"]] = relationship(
        "EventMember",
        primaryjoin=lambda: and_(
            Event.id == foreign(EventMember.event_id),
            EventMember.status == MemberStatus.WAITLIST,
        ),
        viewonly=True,
        order_by="EventMember.joined_date",
        lazy="joined",
    )

    confirmed_members: Mapped[List["EventMember"]] = relationship(
        "EventMember",
        primaryjoin=lambda: and_(
            Event.id == foreign(EventMember.event_id),
            EventMember.status == MemberStatus.CONFIRMED,
        ),
        viewonly=True,
        order_by="EventMember.joined_date",
        lazy="joined",
    )

    hosts: Mapped[List["EventMember"]] = relationship(
        "EventMember",
        primaryjoin=lambda: and_(
            Event.id == foreign(EventMember.event_id),
            EventMember.status == MemberStatus.HOST,
        ),
        viewonly=True,
        order_by="EventMember.joined_date",
        lazy="joined",
    )

    wines: Mapped[List["EventWine"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", lazy="joined"
    )

    bot_messages: Mapped[List["BotMessage"]] = relationship(
        "BotMessage",
        back_populates="event",
        foreign_keys="BotMessage.event_id",
        primaryjoin="and_(Event.id == BotMessage.event_id, BotMessage.message_type == 'event')",
        cascade="all, delete-orphan",
    )
