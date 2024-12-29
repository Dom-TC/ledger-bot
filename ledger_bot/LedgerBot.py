"""The LedgerBot class is the actual implimentation of the Discord bot.  Extends discord.Client."""

import logging
from typing import Any, Dict

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .clients import ExtendedClient, ReactionRolesClient, TransactionsClient
from .process_dm import is_dm, process_dm
from .process_message import process_message
from .reminder_manager import ReminderManager
from .storage import TransactionStorage, ReactionRolesStorage

log = logging.getLogger(__name__)


class LedgerBot(TransactionsClient, ReactionRolesClient, ExtendedClient):
    def __init__(
        self,
        config: Dict[str, Any],
        transaction_storage: TransactionStorage,
        reaction_roles_storage: ReactionRolesStorage,
        scheduler: AsyncIOScheduler,
        reminders: ReminderManager,
    ) -> None:
        self.config = config
        self.transaction_storage = transaction_storage
        self.reaction_roles_storage = reaction_roles_storage
        self.scheduler = scheduler
        self.reminders = reminders

        # We need a guild object for various uses but can't get the full guild object until the bot is connected and on_ready is called, so use this as a tempory object.
        self.guild = discord.Object(id=self.config["guild"])

        log.info(f"Set guild: {self.config['guild']}")
        log.info(f"Watching channels: {self.config['channels']}")

        intents = discord.Intents(
            messages=True,
            guilds=True,
            reactions=True,
            message_content=True,
            members=True,
        )

        super().__init__(
            intents=intents,
            config=self.config,
            scheduler=self.scheduler,
            reaction_roles_storage=self.reaction_roles_storage,
            transaction_storage=self.transaction_storage,
            reminders=self.reminders,
        )

    async def on_ready(self) -> None:
        log.info(f"We have logged in as {self.user}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=self.config["watching_status"],
            )
        )

        # Properly set the guild object
        self.guild = self.get_guild(self.config["guild"])

        log.info("Building slash commands")
        await self.tree.sync(guild=self.guild)

        self.scheduler.start()

        if not self.scheduler.running:
            log.warning("The scheduler is not running")

    async def on_message(self, message: discord.Message) -> None:
        # Process DMs
        if is_dm(message):
            await process_dm(self, message)
            return

        if isinstance(message.channel, (discord.DMChannel, discord.PartialMessageable)):
            log.info("Can't get channel name, skipping...")
            return

        channel_name = message.channel.name

        if (
            self.config["channels"].get("include")
            and channel_name not in self.config["channels"]["include"]
        ):
            return
        else:
            if channel_name in self.config["channels"].get("exclude", []):
                return

        # Process messages
        await process_message(self, message)

    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        channel = await self.get_or_fetch_channel(payload.channel_id)
        reactor = payload.member
        guild_id = payload.guild_id

        if reactor is None:
            log.warning("Payload contained no reactor. Ignoring payload.")
            return

        if not isinstance(channel, discord.TextChannel):
            log.warning("Couldn't get channel information. Ignoring reaction.")
            return

        if guild_id is None:
            log.debug("Reaction on non-guild message. Ignoring")
            return

        guild = self.get_guild(guild_id)
        if guild is None:
            log.error(f"Guild with ID '{guild_id}' not found!")
            return

        hangled_transaction_reaction = await self.handle_transaction_reaction(payload)
        if hangled_transaction_reaction:
            return

        handled_role_reaction = await self.handle_role_reaction(payload)
        if handled_role_reaction:
            return

        log.info(f"Failed to match any commands on {payload.emoji}")

    async def on_raw_reaction_remove(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        channel = await self.get_or_fetch_channel(payload.channel_id)
        reactor = payload.user_id
        guild_id = payload.guild_id

        log.debug(payload)

        if reactor is None:
            log.warning("Payload contained no reactor. Ignoring payload.")
            return

        if not isinstance(channel, discord.TextChannel):
            log.warning("Couldn't get channel information. Ignoring reaction removal.")
            return

        if guild_id is None:
            log.debug("Reaction removal on non-guild message. Ignoring")
            return

        guild = self.get_guild(guild_id)
        if guild is None:
            log.error(f"Guild with ID '{guild_id}' not found!")
            return

        handled_role_reaction_removal = await self.handled_role_reaction_removal(
            payload
        )
        if handled_role_reaction_removal:
            return

        log.info(f"Failed to match any commands on {payload.emoji} removal")

    async def on_disconnect(self) -> None:
        log.warning("Bot disconnected")
