"""The data model for a record in the `event_deposits` table."""

import logging
from dataclasses import dataclass
from datetime import datetime
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
    paid_date: datetime | None = None
    confirmed_paid_date: datetime | None = None
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
            paid_date=datetime.strptime(
                fields.get("paid_date"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            confirmed_paid_date=datetime.strptime(
                fields.get("confirmed_paid_date"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            bot_id=fields.get("bot_id"),
        )
