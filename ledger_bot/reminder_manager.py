"""Classing for managing Reminders."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

import arrow
import discord
from apscheduler import events
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .message_generators import generate_reminder_status_message
from .models import BotMessage, Reminder, Transaction
from .storage import AirtableStorage

if TYPE_CHECKING:
    from .LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class ReminderManager:
    """Deals with all schedules relating to sending reminders."""

    def __init__(
        self,
        config: Dict[str, Any],
        scheduler: AsyncIOScheduler,
        storage: AirtableStorage,
    ):
        self.config = config
        self.scheduler = scheduler
        self.storage = storage
        self.missed_job_ids: List[str] = []
        self.get_channel_func = None

        initial_refresh_time = arrow.utcnow().shift(minutes=1).datetime
        scheduler.add_job(
            self.refresh_reminders,
            name="Refresh Reminders",
            trigger="cron",
            hour=config["reminder_refresh_time"]["hour"],
            minute=config["reminder_refresh_time"]["minute"],
            second=config["reminder_refresh_time"]["second"],
            coalesce=True,
            next_run_time=initial_refresh_time,
        )

        scheduler.add_listener(self.handle_scheduler_event, events.EVENT_JOB_MISSED)

    def set_client(self, client: "LedgerBot") -> None:
        self.client = client

    def handle_scheduler_event(self, event: events.JobEvent) -> None:
        """Handle events from scheduler."""
        job = self.scheduler.get_job(event.job_id)
        if job is not None and job.name.startswith("Reminder:"):
            log.debug(f"Adding job {event.job_id} to missed_job_ids")
            self.missed_job_ids.append(event.job_id)

    async def refresh_reminders(self) -> None:
        """Creates jobs for all stored reminders."""
        reminders_processed = 0
        async for reminder in self.storage.retrieve_reminders():
            self.scheduler.add_job(
                self.send_reminder,
                id=reminder.record_id,
                name=f"Reminder: {reminder.record_id}-{reminder.row_id}",
                trigger="date",
                next_run_time=reminder.date,
                coalesce=True,
                replace_existing=True,
                kwargs={
                    "reminder_id": reminder.record_id,
                    "member_id": reminder.member_id,
                    "transaction_id": reminder.transaction_id,
                    "status": reminder.status,
                },
            )
            reminders_processed += 1
        log.debug(f"Refreshed {reminders_processed} reminders")

    async def send_reminder(
        self, reminder_id: str, member_id: str, transaction_id: str, status: str
    ) -> None:
        log.debug(f"reminder_id: {reminder_id}")
        log.debug(f"member_id: {member_id}")
        log.debug(f"transaction_id: {transaction_id}")
        log.debug(f"status: {status}")

        member_record = await self.storage.get_member_from_record_id(member_id[0])

        log.debug(f"{member_record} / {type(member_record)}")

        user = await self.client.get_or_fetch_user(member_record.discord_id)

        log.info(f"Sending reminder '{reminder_id}' to {user.name}")

        # Get transaction record from record_id transaction_id[0]
        transaction_record = await self.storage.get_transaction_from_record_id(
            transaction_id[0]
        )

        # Filter if matched status
        match status:
            case "approved":
                if transaction_record.sale_approved:
                    log.info("Skipping reminder - approved")
                    return
            case "cancelled":
                if transaction_record.cancelled:
                    log.info("Skipping reminder - cancelled")
                    return
            case "completed":
                if (
                    transaction_record.sale_approved
                    and transaction_record.buyer_marked_delivered
                    and transaction_record.seller_marked_delivered
                    and transaction_record.buyer_marked_paid
                    and transaction_record.seller_marked_paid
                ):
                    log.info("Skipping reminder - completed")
                    return

            case "delivered":
                if (
                    transaction_record.buyer_marked_delivered
                    and transaction_record.seller_marked_delivered
                ):
                    log.info("Skipping reminder - delivered")
                    return

            case "paid":
                if (
                    transaction_record.buyer_marked_paid
                    and transaction_record.seller_marked_paid
                ):
                    log.info("Skipping reminder - paid")
                    return

        if transaction_record.seller_discord_id is None:
            log.warning("No Seller Discord ID specified. Skipping")
            return

        if transaction_record.buyer_discord_id is None:
            log.warning("No Buyer Discord ID specified. Skipping")
            return

        status_message = generate_reminder_status_message(
            seller=await self.client.get_or_fetch_user(
                transaction_record.seller_discord_id
            ),
            buyer=await self.client.get_or_fetch_user(
                transaction_record.buyer_discord_id
            ),
            wine_name=transaction_record.wine,
            wine_price=transaction_record.price,
            config=self.config,
            is_approved=transaction_record.sale_approved,
            is_marked_paid_by_buyer=transaction_record.buyer_marked_paid,
            is_marked_paid_by_seller=transaction_record.seller_marked_paid,
            is_marked_delivered_by_buyer=transaction_record.buyer_marked_delivered,
            is_marked_delivered_by_seller=transaction_record.seller_marked_delivered,
            is_cancelled=transaction_record.cancelled,
        )

        link = None
        if transaction_record.bot_messages is not None:
            latest_message_record_id = transaction_record.bot_messages[-1]
            if isinstance(latest_message_record_id, str):
                message_record = await self.storage.find_bot_message_by_record_id(
                    latest_message_record_id
                )
                message = BotMessage.from_airtable(message_record)
            else:
                message = latest_message_record_id

            link = f"\n\n https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.bot_message_id}"

        await user.send(f"This is your scheduled reminder.\n{status_message}{link}")

    async def create_reminder(
        self,
        reminder: Reminder | None,
        date: datetime | None = None,
        member: discord.Member | None = None,
        transaction: Transaction | None = None,
        status: str | None = None,
    ) -> Reminder:
        """
        Add a reminder to the store and schedule it.

        Parameters
        ----------
        member : discord.Member
            The user creating the reminder
        transaction : Transaction
            The transaction the user wants to be reminded of
        status : Optional[str], optional
            An optional status filter, by default None
        """
        if reminder is None:
            log.debug("Reminder object not provided, building from components.")

            if not (date and member and transaction):
                log.error(
                    f"date, member, and transaction must all be provided if dynamically building reminder object. Received {date} / {member} / {transaction}."
                )
                raise ValueError

            if transaction.record_id is None:
                log.error("Transaction has no record ID.")
                raise ValueError

            member_record = await self.storage.get_or_add_member(member)

            # Build Transaction object from provided data
            reminder = Reminder(
                date=date,
                member_id=member_record.record_id,
                transaction_id=transaction.record_id,
                status=status,
            )

        reminder_fields = ["date", "member_id", "transaction_id", "status", "bot_id"]
        log.debug(f"Creating reminder: {reminder}, with fields {reminder_fields}")

        reminder_record = await self.storage.save_reminder(
            reminder=reminder, fields=reminder_fields
        )

        created_reminder = Reminder.from_airtable(reminder_record)

        log.info(f"Created reminder {created_reminder}")
        return created_reminder

    async def list_reminders(self) -> NotImplementedError:
        raise NotImplementedError

    async def remove_reminder(self) -> NotImplementedError:
        raise NotImplementedError
