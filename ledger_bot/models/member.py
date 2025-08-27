"""The data model for a record in the `members` table."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event
    from .event_member import EventMember
    from .event_wine import EventWine
    from .reminder import Reminder
    from .transaction import Transaction

log = logging.getLogger(__name__)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column(String, nullable=False)
    discord_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    nickname: Mapped[Optional[str]] = mapped_column(String)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    dietary_requirements: Mapped[str] = mapped_column(String, nullable=True)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    attending_events: Mapped[List["EventMember"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )
    wines_brought_to_events: Mapped[List["EventWine"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )
    hosted_events: Mapped[List["Event"]] = relationship(
        back_populates="host", foreign_keys="Event.host_id"
    )
    selling_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="seller",
        foreign_keys="Transaction.seller_id",
        cascade="all, delete-orphan",
    )
    buying_transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="buyer",
        foreign_keys="Transaction.buyer_id",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[List["Reminder"]] = relationship(
        "Reminder",
        back_populates="member",
        foreign_keys="Reminder.member_id",
        cascade="all, delete-orphan",
    )

    @property
    def display_name(self) -> str:
        """Return the nickname if set, otherwise the username."""
        return self.nickname if self.nickname else self.username
