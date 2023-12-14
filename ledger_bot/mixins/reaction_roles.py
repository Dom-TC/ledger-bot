"""A mixin for dealing with reaction roles."""

import logging
from datetime import datetime, timedelta

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ledger_bot.storage import ReactionRolesStorage

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class ReactionRoles(ExtendedClient):
    def __init__(
        self,
        scheduler: AsyncIOScheduler,
        reactions_roles_storage: ReactionRolesStorage,
        **kwargs,
    ):
        self.reactions_roles_storage = reactions_roles_storage
        scheduler.add_job(
            self.refresh_reaction_role_caches,
            name="Refresh reaction-role watched messages and approval channels",
            trigger="cron",
            minute="*/30",
            coalesce=True,
            next_run_time=datetime.now() + timedelta(seconds=5),
            misfire_grace_time=10,
        )
        super().__init__(**kwargs)

    async def refresh_reaction_role_caches(self):
        log.info("Refreshing reaction-role watched messages")
        self.reactions_roles_storage.list_watched_message_ids()

    async def handle_role_reaction(self, payload: discord.RawReactionActionEvent):
        raise NotImplementedError
