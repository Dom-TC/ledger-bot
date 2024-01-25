"""A mixin for dealing with events."""

import logging
from typing import Any, Dict

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ledger_bot.models import Event, EventDeposit, EventWine
from ledger_bot.storage import EventStorage

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class EventsClient(ExtendedClient):
    def __init__(
        self,
        config: Dict[str, Any],
        scheduler: AsyncIOScheduler,
        event_storage: EventStorage,
        **kwargs,
    ) -> None:
        self.config = config
        self.scheduler = scheduler
        self.event_storage = event_storage

        super().__init__(config=config, scheduler=scheduler, **kwargs)
