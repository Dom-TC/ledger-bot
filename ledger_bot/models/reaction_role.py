"""The data model for a record in the `reaction_roles` table."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

log = logging.getLogger(__name__)


@dataclass
class ReactionRole:
    server_id: int
    message_id: int
    reaction_name: str
    role_id: int
    record_id: str | None = None
    row_id: int | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "ReactionRole":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            server_id=int(fields["server_id"]),
            message_id=int(fields["message_id"]),
            reaction_name=fields["reaction_name"],
            role_id=int(fields["role_id"]),
            row_id=int(fields["row_id"]),
            bot_id=fields.get("bot_id"),
        )
