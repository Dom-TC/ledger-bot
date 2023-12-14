"""The data model for a record in the `reaction_roles` table."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

log = logging.getLogger(__name__)


@dataclass
class ReactionRole:
    server_id: str
    message_id: int
    reaction_name: str
    role_id: str
    record_id: str | None = None
    row_id: str | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "ReactionRole":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            server_id=fields["server_id"],
            message_id=fields["message_id"],
            reaction_name=fields["reaction_name"],
            role_id=fields["role_id"],
            row_id=fields["row_id"],
            bot_id=fields["bot_id"],
        )
