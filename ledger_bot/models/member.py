"""The data model for a record in the `members` table."""

import logging
from dataclasses import dataclass
from typing import List

log = logging.getLogger(__name__)


@dataclass
class Member:
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
    def from_airtable(cls, data: dict) -> "Member":
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
    def display_name(self):
        name = self.nickname if self.nickname else self.username
        return f"{name}"
