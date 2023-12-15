"""A mixin for dealing with transactions."""

import logging
from typing import Any, Dict

import arrow
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import app_commands

from ledger_bot.models import Member
from ledger_bot.process_dm import is_dm, process_dm
from ledger_bot.process_message import process_message
from ledger_bot.process_transactions import (
    approve_transaction,
    cancel_transaction,
    mark_transaction_delivered,
    mark_transaction_paid,
)
from ledger_bot.reactions import add_reaction, remove_reaction
from ledger_bot.reminder_manager import ReminderManager
from ledger_bot.scheduled_commands import cleanup
from ledger_bot.storage import AirtableStorage
from ledger_bot.views import CreateReminderButton

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class TransactionsClient(ExtendedClient):
    def __init__(
        self,
        config: Dict[str, Any],
        scheduler: AsyncIOScheduler,
        transaction_storage: AirtableStorage,
        reminders: ReminderManager,
        **kwargs,
    ) -> None:
        self.config = config
        self.scheduler = scheduler
        self.transaction_storage = transaction_storage
        self.reminders = reminders

        scheduler.add_job(
            func=cleanup,
            name="Cleanup",
            kwargs={"client": self, "storage": self.transaction_storage},
            trigger="cron",
            hour=config["run_cleanup_time"]["hour"],
            minute=config["run_cleanup_time"]["minute"],
            second=config["run_cleanup_time"]["second"],
            timezone="UTC",
        )
        super().__init__(config=config, scheduler=scheduler, **kwargs)

    async def handle_transaction_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        channel = await self.get_or_fetch_channel(payload.channel_id)
        reactor = payload.member

        # Check if valid reaction emoji
        if payload.emoji.name not in [
            self.config["emojis"]["approval"],
            self.config["emojis"]["cancel"],
            self.config["emojis"]["paid"],
            self.config["emojis"]["delivered"],
            self.config["emojis"]["reminder"],
        ]:
            return False

        # Check if in valid channel
        if (
            self.config["channels"].get("include")
            and channel.name not in self.config["channels"]["include"]
        ):
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel not included"
            )
            return False
        else:
            if channel.name in self.config["channels"].get("exclude", []):
                log.info(
                    f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel excluded"
                )
                return False

        # Check if valid message
        target_transaction = (
            await self.transaction_storage.find_transaction_by_bot_message_id(
                str(payload.message_id)
            )
        )
        if target_transaction is None:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Invalid target message"
            )
            return False

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
        buyer_id = await self.transaction_storage.get_member_from_record_id(
            target_transaction.buyer_id.record_id
            if isinstance(target_transaction.buyer_id, Member)
            else target_transaction.buyer_id
        )
        buyer = await self.get_or_fetch_user(buyer_id.discord_id)
        seller_id = await self.transaction_storage.get_member_from_record_id(
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
            return False

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
                storage=self.transaction_storage,
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
                storage=self.transaction_storage,
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
                storage=self.transaction_storage,
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
                storage=self.transaction_storage,
            )

        elif payload.emoji.name == self.config["emojis"]["reminder"]:
            # Watch
            log.info(
                f"Processing reminder reaction from {reactor.name} on message {payload.message_id}"
            )
            await reactor.send(
                content=f'Click here to add a reminder for "*{target_transaction.wine}*" from {buyer.mention} to {seller.mention} for £{target_transaction.price}',
                view=CreateReminderButton(
                    storage=self.transaction_storage,
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

        log.info(f"Finished processing reaction {payload.emoji} from {reactor}")
        return True
