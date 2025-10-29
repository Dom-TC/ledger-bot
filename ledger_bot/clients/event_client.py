"""A mixin for dealing with events."""

import logging

import arrow
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.core import Config
from ledger_bot.services import Service

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class EventClient(ExtendedClient):
    def __init__(
        self,
        config: Config,
        scheduler: AsyncIOScheduler,
        service: Service,
        session_factory: async_sessionmaker[AsyncSession],
        **kwargs,
    ) -> None:
        self.config = config
        self.scheduler = scheduler
        self.service = service
        self.session_factory = session_factory

        super().__init__(
            config=config,
            scheduler=scheduler,
            service=service,
            session_factory=session_factory,
            **kwargs,
        )

    async def handle_event_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        log.debug("Running handle_event_reaction")

        return False
