"""The data model for a record in the `event_wines` table."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from .member import Member

log = logging.getLogger(__name__)


@dataclass
class EventWine:
    event_id: str
    member: str | Member
    wine: str
    record_id: str | None = None
    row_id: int | None = None
    creation_date: datetime | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "EventWine":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            event_id=fields.get("event_id"),
            member=fields.get("member"),
            wine=fields.get("wine"),
            creation_date=datetime.strptime(
                fields.get("creation_date"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            bot_id=fields.get("bot_id"),
        )
