"""The data model for a record in the `members` table."""

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class Member:
    record_id: str
    row_id: str
    discord_id: int
    username: str
    nickname: str
    sell_transactions: str
    buy_transactions: str
    bot_id: str

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
            bot_id=fields.get("bot_id"),
        )

    @property
    def display_name(self):
        name = self.nickname if self.nickname else self.username
        return f"{name}"
