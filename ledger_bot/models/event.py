"""The data model for a record in the `events` table."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .event_deposit import EventDeposit
from .event_wine import EventWine
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
    guests: list[str | Member] | None = None
    guests_count: int = 0
    is_private: bool = False
    location: str | None = None
    channel_id: str | None = None
    is_archived: bool = False
    deposit_amount: float | None = None
    event_deposits: list[str | EventDeposit] | None = None
    event_wines: list[str | EventWine] | None = None
    creation_date: datetime | None = None
    archived_date: datetime | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: dict[str, Any]) -> Event:
        """Converts the dict returned by AirTable into an Event object.

        Parameters
        ----------
        data : dict[str, Any]
            The data provided by AirTable

        Returns
        -------
        Event
            The event object
        """
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            event_name=fields.get("event_name"),
            host=fields.get("host"),
            event_date=datetime.strptime(
                fields.get("event_date"), "%Y-%m-%dT%H:%M:%S.%f%z"
            ),
            max_guests=(
                int(fields.get("max_guests"))
                if fields.get("max_guests") is not None
                else None
            ),
            guests=fields.get("guests"),
            guests_count=int(fields.get("guests_count", 0)),
            is_private=bool(fields.get("is_archived", False)),
            is_archived=bool(fields.get("is_archived", False)),
            location=fields.get("location"),
            channel_id=fields.get("channel_id"),
            deposit_amount=(
                float(fields.get("deposit_amount"))
                if fields.get("deposit_amount") is not None
                else None
            ),
            event_deposits=fields.get("event_deposits"),
            event_wines=fields.get("event_wines"),
            creation_date=(
                datetime.strptime(fields.get("creation_date"), "%Y-%m-%dT%H:%M:%S.%f%z")
                if fields.get("creation_date") is not None
                else None
            ),
            archived_date=(
                datetime.strptime(fields.get("archived_date"), "%Y-%m-%dT%H:%M:%S.%f%z")
                if fields.get("archived_date") is not None
                else None
            ),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields: list[str] | None = None) -> dict[str, Any]:
        """Convert the Event object into a dict ready to be provided to AirTable.

        Parameters
        ----------
        fields : List[str] | None, optional
            A list of what fields to include in include in the final dictionary. Useful for only updating certain portions of a row.
            If fields is None, the entire model is included in the final dictionay.

        Returns
        -------
        Dict[str, Any]
            A dictionary ready to be sent to AirTable.
        """
        fields = (
            fields
            if fields
            else [
                "event_name",
                "host",
                "event_date",
                "max_guests",
                "guests",
                "is_private",
                "is_archived",
                "location",
                "channel_id",
                "deposit_amount",
                "event_deposits",
                "event_wines",
                "creation_date",
                "archived_date",
                "bot_id",
            ]
        )

        data: dict[str, str | list[str]] = {}

        if "host" in fields:
            data["host"] = (
                str(self.host.record_id) if isinstance(self.host, Member) else self.host
            )

        if "guests" in fields and self.guests is not None:
            guests_list = []
            for guest in self.guests:
                guests_list.append(
                    guest.record_id
                    if isinstance(guest, Member) and guest.record_id
                    else str(guest)
                )

            data["guests"] = guests_list

        if "event_deposits" in fields and self.event_deposits is not None:
            event_deposits_list = []
            for event_deposit in self.event_deposits:
                event_deposits_list.append(
                    str(event_deposit.record_id)
                    if isinstance(event_deposit, EventDeposit)
                    else event_deposit
                )
            data["event_deposits"] = event_deposits_list

        if "event_wines" in fields and self.event_wines is not None:
            event_wines_list = []
            for event_wine in self.event_wines:
                event_wines_list.append(
                    str(event_wine.record_id)
                    if isinstance(event_wine, EventWine)
                    else event_wine
                )
            data["event_wines"] = event_wines_list

        # For any attribute which is just assigned, without alteration we can list it here and iterate through the list
        # ie. anywhere we would do `data[attr] = self.attr`
        str_conversions = [
            "event_name",
            "location",
            "channel_id",
            "max_guests",
            "bot_id",
            "event_date",
            "deposit_amount",
            "creation_date",
            "archived_date",
        ]
        for attr in str_conversions:
            if attr in fields:
                data[attr] = str(getattr(self, attr))

        bare_conversions = [
            "is_private",
            "is_archived",
        ]
        for attr in bare_conversions:
            if attr in fields:
                data[attr] = getattr(self, attr)

        return {
            "id": self.record_id,
            "fields": data,
        }
