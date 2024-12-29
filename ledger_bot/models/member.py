"""The data model for a record in the `members` table."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from .event import Event
    from .event_deposit import EventDeposit
    from .event_wine import EventWine

log = logging.getLogger(__name__)


@dataclass
class Member:
    username: str
    discord_id: int
    record_id: str | None = None
    row_id: str | None = None
    nickname: str | None = None
    sell_transactions: list[str] | None = None
    buy_transactions: list[str] | None = None
    host_events: list[str | Event] | None = None
    guest_events: list[str | Event] | None = None
    event_wines: list[str | EventWine] | None = None
    event_deposits: list[str | EventDeposit] | None = None
    reminders: list[str] | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: dict[str, Any]) -> Member:
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            username=fields.get("username"),
            discord_id=int(fields.get("discord_id")),
            nickname=fields.get("nickname"),
            sell_transactions=fields.get("sell_transactions"),
            buy_transactions=fields.get("buy_transactions"),
            host_events=fields.get("host_events"),
            guest_events=fields.get("guest_events"),
            event_wines=fields.get("event_wines"),
            event_deposits=fields.get("event_deposits"),
            reminders=fields.get("reminders"),
            bot_id=fields.get("bot_id"),
        )

    @property
    def display_name(self) -> str:
        name = self.nickname if self.nickname else self.username
        return f"{name}"
