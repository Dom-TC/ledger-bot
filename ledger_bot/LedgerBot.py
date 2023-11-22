"""The LedgerBot class is the actual implimentation of the Discord bot.  Extends discord.Client."""

import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord import app_commands

from .process_dm import is_dm, process_dm
from .process_transactions import (
    approve_transaction,
    cancel_transaction,
    mark_transaction_delivered,
    mark_transaction_paid,
)
from .processs_message import process_message
from .reminder_manager import ReminderManager
from .scheduled_commands import cleanup
from .storage import AirtableStorage
from .views import CreateReminderButton

log = logging.getLogger(__name__)


class LedgerBot(discord.Client):
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
        config: dict,
        storage: AirtableStorage,
        scheduler: AsyncIOScheduler,
        reminders: ReminderManager,
    ):
        self.config = config
        self.storage = storage
        self.guild = discord.Object(id=self.config["guild"])
        self.scheduler = scheduler
        self.reminders = reminders

        log.info(f"Set guild: {self.config['guild']}")
        log.info(f"Watching channels: {self.config['channels']}")

        intents = discord.Intents(
            messages=True, guilds=True, reactions=True, message_content=True
        )

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

        scheduler.start()

        if not scheduler.running:
            log.warning("The scheduler is not running")

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        log.info(f"We have logged in as {self.user}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=self.config["watching_status"],
            )
        )

        log.info("Building slash commands")
        await self.tree.sync(guild=self.guild)

    async def on_message(self, message):
        # Process DMs
        if is_dm(message):
            await process_dm(self, message)
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

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Check if valid reaction emoji
        if payload.emoji.name not in [
            self.config["emojis"]["approval"],
            self.config["emojis"]["cancel"],
            self.config["emojis"]["paid"],
            self.config["emojis"]["delivered"],
            self.config["emojis"]["reminder"],
        ]:
            return

        channel = self.get_channel(payload.channel_id)
        reactor = payload.member

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
        if target_transaction.buyer_id is None:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Target message doesn't contain valid buyer_id"
            )
            return
        if target_transaction.seller_id is None:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Target message doesn't contain valid seller_id"
            )
            return

        # Get buyer & seller discord.Member objects
        buyer_id = await self.storage.get_member_from_record_id(
            target_transaction.buyer_id
        )
        buyer = await self.fetch_user(buyer_id.discord_id)
        seller_id = await self.storage.get_member_from_record_id(
            target_transaction.seller_id
        )
        seller = await self.fetch_user(seller_id.discord_id)

        # Check if buyer or seller
        if reactor.id != buyer.id and reactor.id != seller.id:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Reactor is neither buyer nor seller"
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

    async def on_disconnect(self):
        log.warning("Bot disconnected")
