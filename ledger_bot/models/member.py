"""The data model for a record in the `members` table."""

import datetime
import logging
from typing import TYPE_CHECKING, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, Integer, String, and_
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ledger_bot.utils import resolve_timezone

from .base import Base
from .event import Event
from .event_member import EventMember
from .event_wine import EventWine

if TYPE_CHECKING:
    from .reminder import Reminder
    from .transaction import Transaction

from .event_member import MemberStatus

log = logging.getLogger(__name__)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column(String, nullable=False)
    discord_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    nickname: Mapped[Optional[str]] = mapped_column(String)
    creation_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )
    dietary_requirements: Mapped[str] = mapped_column(String, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lookup_enabled: Mapped[bool] = mapped_column(Integer, default=1)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
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

    attending_events: Mapped[List["EventMember"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )
    hosted_events: Mapped[List["Event"]] = relationship(
        "Event",
        secondary="event_members",
        primaryjoin=lambda: and_(
            Member.id == foreign(EventMember.member_id),
            foreign(EventMember.status) == MemberStatus.HOST,
        ),
        secondaryjoin=lambda: foreign(EventMember.event_id) == foreign(Event.id),
        viewonly=True,
    )
    wines_brought_to_events: Mapped[List["EventWine"]] = relationship(
        "EventWine",
        secondary="event_members",
        primaryjoin=lambda: Member.id == foreign(EventMember.member_id),
        secondaryjoin=lambda: foreign(EventMember.id)
        == foreign(EventWine.event_member_id),
        viewonly=True,
    )

    @property
    def display_name(self) -> str:
        """Return the nickname if set, otherwise the username."""
        return self.nickname if self.nickname else self.username

    @property
    def resolve_timezone(self) -> ZoneInfo | datetime.timezone | None:
        return resolve_timezone(self.timezone) if self.timezone else None
