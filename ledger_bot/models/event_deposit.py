"""The data model for a record in the `event_deposits` table."""

import logging
from dataclasses import dataclass
from typing import Any, Dict

from .member import Member

log = logging.getLogger(__name__)


@dataclass
class EventDeposit:
    event_id: str
    member: str | Member
    record_id: int | None = None
    row_id: int | None = None
    paid: bool = False
    confirmed_paid: bool = False
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "EventDeposit":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            event_id=fields.get("event_id"),
            member=fields.get("member"),
            paid=bool(fields.get("paid")),
            confirmed_paid=bool(fields.get("confirmed_paid")),
            bot_id=fields.get("bot_id"),
        )
