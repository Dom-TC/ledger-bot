"""The data model for a record in the `bot_messages` table."""

import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class BotMessage:
    record_id: str
    row_id: str
    bot_message_id: int
    channel_id: int
    guild_id: int
    transaction_id: str
    message_creation_date: str
    bot_id: str

    @classmethod
    def from_airtable(cls, data: dict) -> "BotMessage":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            bot_message_id=int(fields.get("bot_message_id")),
            channel_id=int(fields.get("channel_id")),
            guild_id=int(fields.get("guild_id")),
            transaction_id=fields.get("transaction_id")[0],
            message_creation_date=fields.get("message_creation_date"),
            bot_id=fields.get("bot_id"),
        )
