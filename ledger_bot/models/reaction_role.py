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
    role_name: str
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
            role_name=fields["role_name"],
            row_id=int(fields["row_id"]),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields: List[str] | None = None) -> Dict[str, Any]:
        fields = (
            fields
            if fields
            else [
                "server_id",
                "message_id",
                "reaction_name",
                "role_id",
                "role_name",
                "bot_id",
            ]
        )

        data: Dict[str, str | List[str]] = {}

        # For any attribute which is just assigned, without alteration we can list it here and iterate through the list
        # ie. anywhere we would do `data[attr] = self.attr`
        bare_conversions = [
            "server_id",
            "message_id",
            "reaction_name",
            "role_id",
            "role_name",
            "bot_id",
        ]
        for attr in bare_conversions:
            if attr in fields:
                data[attr] = str(getattr(self, attr))

        return {
            "id": self.record_id,
            "fields": data,
        }
