"""Mixin for dealing with the Events table."""

import datetime
import logging
from typing import Any, Dict, List, Optional

import discord
from aiohttp import ClientSession

from ledger_bot.models import BotMessage, Event, Transaction

from .base_storage import BaseStorage

log = logging.getLogger(__name__)


class EventsMixin(BaseStorage):
    events_url: str
    bot_id: str

    async def insert_event(
        self, event_record: Dict[str, Any], session: Optional[ClientSession] = None
    ) -> Event:
        record = await self._insert(self.events_url, event_record, session)
        return Event.from_airtable(record)

    async def update_event(
        self,
        record_id: str,
        event_record: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> Event:
        record = await self._update(
            self.events_url + "/" + record_id, event_record, session
        )

        return Event.from_airtable(record)

    async def save_event(self, event: Event, fields: List[str] | None = None) -> Event:
        fields = fields or [
            "event_name",
            "host",
            "event_date",
            "max_guests",
            "guests",
            "location",
            "channel_id",
            "deposit_amount",
            "bot_id",
        ]

        # Always store bot_id
        event.bot_id = self.bot_id or ""
        if "bot_id" not in fields:
            fields.append("bot_id")

        event_data = event.to_airtable(fields=fields)
        log.info(f"Adding event data: {event_data['fields']}")
        if event.record_id:
            log.info(f"Updating event with id: {event_data['id']}")
            return await self.update_event(event_data["id"], event_data["fields"])
        else:
            log.info("Adding event to Airtable")
            return await self.insert_event(event_data["fields"])
