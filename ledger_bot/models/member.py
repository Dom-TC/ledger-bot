"""The data model for a record in the `members` table."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event
    from .event_member import EventMember
    from .event_wine import EventWine

log = logging.getLogger(__name__)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    username: Mapped[str] = mapped_column(String, nullable=False)
    discord_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    nickname: Mapped[Optional[str]] = mapped_column(String)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    attending_events: Mapped[List["EventMember"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )
    wines_brought_to_events: Mapped[List["EventWine"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )
    hosted_events: Mapped[List["Event"]] = relationship(
        back_populates="host", foreign_keys="[Event.host_id]"
    )


@dataclass
class MemberAirtable:
    username: str
    discord_id: int
    record_id: str | None = None
    row_id: str | None = None
    nickname: str | None = None
    sell_transactions: List[str] | None = None
    buy_transactions: List[str] | None = None
    reminders: List[str] | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "MemberAirtable":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            username=fields.get("username"),
            discord_id=int(fields.get("discord_id")),
            nickname=fields.get("nickname"),
            sell_transactions=fields.get("sell_transactions"),
            buy_transactions=fields.get("buy_transactions"),
            reminders=fields.get("reminders"),
            bot_id=fields.get("bot_id"),
        )

    @property
    def display_name(self) -> str:
        name = self.nickname if self.nickname else self.username
        return f"{name}"
