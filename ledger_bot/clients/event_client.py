"""A mixin for dealing with events."""

import logging
from typing import List

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.core import Config
from ledger_bot.managers import EventChannelManager, EventPostManager
from ledger_bot.models import BotMessage, BotMessageType, Event, EventRegion
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

        # Initialize managers
        self.channel_manager = EventChannelManager(client=self, service=service)
        self.post_manager = EventPostManager(client=self, service=service)

    async def handle_event_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        log.debug("Running handle_event_reaction")

        return False

    async def register_regions(self) -> None:
        log.info("Registering all regions.")

        for raw_region in self.config.channels.event_regions:
            region = EventRegion(
                region_name=raw_region.region_name,
                new_event_category=raw_region.new_event_category,
                event_signup_channel=raw_region.event_signup_channel,
            )

            region = await self.service.event_region.add_or_update_region(region)

            if region.id:
                log.info(
                    f"Successfully added region: {region.region_name} ({region.id})"
                )

    # Delegate channel operations to channel_manager
    async def create_event_channel(
        self, event: Event, session: AsyncSession | None = None
    ) -> discord.TextChannel | None:
        """Create a Discord channel for an event.

        Delegates to EventChannelManager.create_event_channel().
        """
        return await self.channel_manager.create_event_channel(event, session)

    async def update_channel_name(self, event: Event) -> discord.TextChannel | None:
        """Update the name of a Discord channel to match the event's current name.

        Delegates to EventChannelManager.update_channel_name().
        """
        return await self.channel_manager.update_channel_name(event)

    # Delegate post operations to post_manager
    async def update_event_posts(self, event: Event) -> List[discord.Message] | None:
        """Update the posts for a given event.

        Delegates to EventPostManager.update_event_posts().
        """
        return await self.post_manager.update_event_posts(event)

    async def create_event_post(
        self,
        event: Event,
        channel: discord.TextChannel | int,
        message_type: BotMessageType,
        should_pin: bool = False,
    ) -> BotMessage | None:
        """Create a post for a given event.

        Delegates to EventPostManager.create_event_post().
        """
        return await self.post_manager.create_event_post(
            event, channel, message_type, should_pin
        )
