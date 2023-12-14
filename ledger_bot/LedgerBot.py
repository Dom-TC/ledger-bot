"""The LedgerBot class is the actual implimentation of the Discord bot.  Extends discord.Client."""

import logging
from typing import Any, Dict

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import app_commands

from .mixins import ExtendedClient, ReactionRoles
from .models import Member
from .process_dm import is_dm, process_dm
from .process_message import process_message
from .process_transactions import (
    approve_transaction,
    cancel_transaction,
    mark_transaction_delivered,
    mark_transaction_paid,
)
from .reactions import add_reaction, remove_reaction
from .reminder_manager import ReminderManager
from .scheduled_commands import cleanup
from .storage import AirtableStorage, ReactionRolesStorage
from .views import CreateReminderButton

log = logging.getLogger(__name__)


class LedgerBot(ReactionRoles, ExtendedClient):
    """
    The main bot class.

    Paramaters
    ----------
    config : dict
        The bots config options

    storage : storage.AirtableStorage
        The AirTable storage

    guild : discord.Object
        The Discord Server the bot is running in

    scheduler : apscheduler.schedulers.asyncio.AsyncIOScheduler
        The scheduler object

    """

    def __init__(
        self,
        config: Dict[str, Any],
        storage: AirtableStorage,
        reaction_roles_storage: ReactionRolesStorage,
        scheduler: AsyncIOScheduler,
        reminders: ReminderManager,
    ) -> None:
        self.config = config
        self.storage = storage
        self.reaction_roles_storage = reaction_roles_storage
        self.guild = discord.Object(id=self.config["guild"])
        self.scheduler = scheduler
        self.reminders = reminders

        log.info(f"Set guild: {self.config['guild']}")
        log.info(f"Watching channels: {self.config['channels']}")

        log.info("Scheduling jobs...")
        scheduler.add_job(
            func=cleanup,
            name="Cleanup",
            kwargs={"client": self, "storage": self.storage},
            trigger="cron",
            hour=config["run_cleanup_time"]["hour"],
            minute=config["run_cleanup_time"]["minute"],
            second=config["run_cleanup_time"]["second"],
            timezone="UTC",
        )

        intents = discord.Intents(
            messages=True, guilds=True, reactions=True, message_content=True
        )

        super().__init__(
            intents=intents,
            config=self.config,
            scheduler=self.scheduler,
            reaction_roles_storage=self.reaction_roles_storage,
        )

        scheduler.start()

        if not scheduler.running:
            log.warning("The scheduler is not running")

    async def on_ready(self) -> None:
        log.info(f"We have logged in as {self.user}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=self.config["watching_status"],
            )
        )

        log.info("Building slash commands")
        await self.tree.sync(guild=self.guild)

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

        handled_role_reaction = await self.handle_role_reaction(payload)
        if handled_role_reaction:
            return

        # Check if valid reaction emoji
        if payload.emoji.name not in [
            self.config["emojis"]["approval"],
            self.config["emojis"]["cancel"],
            self.config["emojis"]["paid"],
            self.config["emojis"]["delivered"],
            self.config["emojis"]["reminder"],
        ]:
            return

        # Check if in valid channel
        if (
            self.config["channels"].get("include")
            and channel.name not in self.config["channels"]["include"]
        ):
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel not included"
            )
            return
        else:
            if channel.name in self.config["channels"].get("exclude", []):
                log.info(
                    f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel excluded"
                )
                return

        # Check if valid message
        target_transaction = await self.storage.find_transaction_by_bot_message_id(
            str(payload.message_id)
        )
        if target_transaction is None:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Invalid target message"
            )
            return

        # After this point all are checks are slow, so we add the reaction now.
        # The valid message check above is also pretty slow, but we'd then add the reaction to every message that received 👍
        # So we add this after those checks
        await add_reaction(
            client=self,
            message_id=payload.message_id,
            reaction=self.config["emojis"]["thinking"],
            channel_obj=channel,
        )

        # Get buyer & seller discord.Member objects
        buyer_id = await self.storage.get_member_from_record_id(
            target_transaction.buyer_id.record_id
            if isinstance(target_transaction.buyer_id, Member)
            else target_transaction.buyer_id
        )
        buyer = await self.get_or_fetch_user(buyer_id.discord_id)
        seller_id = await self.storage.get_member_from_record_id(
            target_transaction.seller_id.record_id
            if isinstance(target_transaction.seller_id, Member)
            else target_transaction.seller_id
        )
        seller = await self.get_or_fetch_user(seller_id.discord_id)

        # Check if buyer or seller
        if reactor.id != buyer.id and reactor.id != seller.id:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Reactor is neither buyer nor seller"
            )
            await remove_reaction(
                client=self,
                message_id=payload.message_id,
                reaction=self.config["emojis"]["thinking"],
            )
            return

        # Process reaction
        log.info(
            f"Processing {payload.emoji.name} from {reactor.name} on message {payload.message_id}"
        )

        if payload.emoji.name == self.config["emojis"]["approval"]:
            # Approval
            log.info(
                f"Processing approval reaction from {reactor.name} on message {payload.message_id}"
            )
            await approve_transaction(
                reactor=reactor,
                buyer=buyer,
                seller=seller,
                payload=payload,
                channel=channel,
                target_transaction=target_transaction,
                config=self.config,
                storage=self.storage,
            )
        elif payload.emoji.name == self.config["emojis"]["paid"]:
            # Paid
            log.info(
                f"Processing payment reaction from {reactor.name} on message {payload.message_id}"
            )
            await mark_transaction_paid(
                reactor=reactor,
                buyer=buyer,
                seller=seller,
                payload=payload,
                channel=channel,
                target_transaction=target_transaction,
                config=self.config,
                storage=self.storage,
            )
        elif payload.emoji.name == self.config["emojis"]["delivered"]:
            # Delivered
            log.info(
                f"Processing delivered reaction from {reactor.name} on message {payload.message_id}"
            )
            await mark_transaction_delivered(
                reactor=reactor,
                buyer=buyer,
                seller=seller,
                payload=payload,
                channel=channel,
                target_transaction=target_transaction,
                config=self.config,
                storage=self.storage,
            )
        elif payload.emoji.name == self.config["emojis"]["cancel"]:
            # Delivered
            log.info(
                f"Processing cancel reaction from {reactor.name} on message {payload.message_id}"
            )
            await cancel_transaction(
                reactor=reactor,
                buyer=buyer,
                seller=seller,
                payload=payload,
                channel=channel,
                target_transaction=target_transaction,
                config=self.config,
                storage=self.storage,
            )

        elif payload.emoji.name == self.config["emojis"]["reminder"]:
            # Watch
            log.info(
                f"Processing reminder reaction from {reactor.name} on message {payload.message_id}"
            )
            await reactor.send(
                content=f'Click here to add a reminder for "*{target_transaction.wine}*" from {buyer.mention} to {seller.mention} for £{target_transaction.price}',
                view=CreateReminderButton(
                    storage=self.storage,
                    transaction=target_transaction,
                    user=reactor,
                    reminders=self.reminders,
                ),
            )

        # Remove our thinking reaction
        await remove_reaction(
            client=self,
            message_id=payload.message_id,
            reaction=self.config["emojis"]["thinking"],
            channel_obj=channel,
        )

    async def on_disconnect(self) -> None:
        log.warning("Bot disconnected")
