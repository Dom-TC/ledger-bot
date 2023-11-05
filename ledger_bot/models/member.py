"""The data model for a record in the `members` table."""

import logging

from .model import Model

log = logging.getLogger(__name__)


class Member(Model):
    attributes = [
        "id",
        "row_id",
        "discord_id",
        "username",
        "nickname",
        "sell_transactions",
        "buy_transactions",
        "bot_id",
    ]

    @classmethod
    def from_airtable(cls, data: dict) -> "Member":
        fields = data["fields"]
        return cls(
            id=data["id"],
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
