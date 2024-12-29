"""The data model for a record in the `events` table."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .member import Member

log = logging.getLogger(__name__)


@dataclass
class Event:
    event_name: str
    host: str | Member
    event_date: datetime
    record_id: str | None = None
    row_id: int | None = None
    max_guests: int | None = None
    guests: List[str] | None = None
    guests_count: int = 0
    location: str = None
    channel_id: str = None
    is_archived: bool = False
    deposit_amount: float | None = None
    event_deposits: List[str] | None = None
    event_wines: List[str] | None = None
    creation_date: datetime | None = None
    archived_date: datetime | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "Event":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            event_name=fields.get("event_name"),
            host=fields.get("host"),
            event_date=datetime.strptime(
                fields.get("event_date"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            max_guests=int(fields.get("max_guests")),
            guests=fields.get("guests"),
            guests_count=int(fields.get("guests_count")),
            location=fields.get("location"),
            channel_id=fields.get("channel_id"),
            is_archived=fields.get("is_archived", False),
            deposit_amount=float(fields.get("deposit_amount")),
            event_deposits=fields.get("event_deposits"),
            event_wines=fields.get("event_wines"),
            creation_date=datetime.strptime(
                fields.get("creation_date"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            archived_date=datetime.strptime(
                fields.get("archive_date"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            bot_id=fields.get("bot_id"),
        )
