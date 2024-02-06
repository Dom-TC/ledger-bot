"""The data model for a record in the `events` table."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .event_deposit import EventDeposit
from .member import Member

log = logging.getLogger(__name__)


@dataclass
class Event:
    event_name: str
    host: str | Member
    event_date: datetime
    record_id: str | None = None
    row_id: int | None = None
    max_attendees: int | None = None
    private: bool = False
    guests: List[str] | None = None
    guests_count: int = 0
    location: str = None
    channel_id: str = None
    deposit_amount: float | None = None
    event_deposits: List[str] | None = None
    event_wines: List[str] | None = None
    creation_date: str | None = None
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
            max_attendees=int(fields.get("max_attendees"))
            if fields.get("max_attendees")
            else None,
            private=bool(fields.get("private")),
            guests=fields.get("guests"),
            guests_count=int(fields.get("guests_count")),
            location=fields.get("location"),
            channel_id=fields.get("channel_id"),
            deposit_amount=float(fields.get("deposit_amount"))
            if fields.get("deposit_amount")
            else None,
            event_deposits=fields.get("event_deposits"),
            event_wines=fields.get("event_wines"),
            creation_date=fields.get("creation_date"),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields: List[str] | None = None) -> Dict[str, Any]:
        fields = (
            fields
            if fields
            else [
                "event_name",
                "host",
                "event_date",
                "max_attendees",
                "private",
                "guests",
                "location",
                "channel_id",
                "deposit_amount",
                "creation_date",
                "bot_id",
            ]
        )

        data: Dict[str, str | List[str]] = {}

        if "host" in fields:
            data["host"] = [
                str(self.host.record_id) if isinstance(self.host, Member) else self.host
            ]

        if "guests" in fields and self.guests is not None:
            guests_list = []
            for guest in self.guests:
                guests_list.append(
                    guest.record_id if isinstance(guest, Member) else guest
                )
            data["guests"] = guests_list

        if "event_deposits" in fields and self.event_deposits is not None:
            event_deposits_list = []
            for event_deposit in self.event_deposits:
                event_deposits_list.append(
                    event_deposit.record_id
                    if isinstance(event_deposit, EventDeposit)
                    else event_deposit
                )
            data["event_deposits"] = event_deposits_list

        if "event_wines" in fields and self.event_wines is not None:
            event_wines_list = []
            for event_wine in self.event_wines:
                event_wines_list.append(
                    event_wine.record_id
                    if isinstance(event_wine, EventDeposit)
                    else event_wine
                )
            data["event_wines"] = event_wines_list

        # For any attribute which is just assigned, without alteration we can list it here and iterate through the list
        # ie. anywhere we would do `data[attr] = self.attr`
        str_conversions = [
            "event_name",
            "location",
            "channel_id",
            "bot_id",
        ]
        for attr in str_conversions:
            if attr in fields:
                data[attr] = str(getattr(self, attr))

        bare_conversions = [
            "event_date",
            "max_attendees",
            "private",
            "deposit_amount",
            "creation_date",
        ]
        for attr in bare_conversions:
            if attr in fields:
                data[attr] = getattr(self, attr)

        return {
            "id": self.record_id,
            "fields": data,
        }
