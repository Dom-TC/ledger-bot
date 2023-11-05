"""The data model for a record in the `bot_messages` table."""

import logging

from .model import Model

log = logging.getLogger(__name__)


class BotMessage(Model):
    attributes = [
        "id",
        "row_id",
        "bot_message_id",
        "channel_id",
        "guild_id",
        "transaction_id",
        "message_creation_date" "bot_id",
    ]

    @classmethod
    def from_airtable(cls, data: dict) -> "BotMessage":
        fields = data["fields"]
        return cls(
            id=data["id"],
            row_id=fields.get("row_id"),
            bot_message_id=fields.get("bot_message_id"),
            channel_id=fields.get("channel_id"),
            guild_id=fields.get("guild_id"),
            transaction_id=fields.get("transaction_id")[0],
            message_creation_date=fields.get("message_creation_date"),
            bot_id=fields.get("bot_id"),
        )
