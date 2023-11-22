"""Classing for managing Reminders."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import discord
from apscheduler import events
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .models import Reminder, Transaction
from .storage import AirtableStorage

log = logging.getLogger(__name__)


class ReminderManager:
    """Deals with all schedules relating to sending reminders."""

    def __init__(
        self,
        config: dict,
        scheduler: AsyncIOScheduler,
        storage: AirtableStorage,
    ):
        self.config = config
        self.scheduler = scheduler
        self.storage = storage
        self.missed_job_ids = []
        self.get_channel_func = None

        initial_refresh_run = datetime.now() + timedelta(minutes=2)
        scheduler.add_job(
            self.refresh_reminders,
            name="Refresh Reminders",
            trigger="cron",
            hour=config["reminder_refresh_time"]["hour"],
            minute=config["reminder_refresh_time"]["minute"],
            second=config["reminder_refresh_time"]["second"],
            coalesce=True,
            next_run_time=initial_refresh_run,
        )

        scheduler.add_listener(self.handle_scheduler_event, events.EVENT_JOB_MISSED)

    def handle_scheduler_event(self, event: events.JobEvent):
        """Handle events from scheduler."""
        job = self.scheduler.get_job(event.job_id)
        if job & job.name.startswith("Reminder:"):
            self.missed_job_ids.append(event.job_id)

    async def refresh_reminders(self):
        """Creates hobs for all stored reminders."""
        reminders_processed = 0
        async for reminder in self.storage.retrieve_reminders():
            self.scheduler.add_job(
                self.send_reminder,
                id=reminder.id,
                name=f"Reminder: {reminder.transaction_id}!",
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

    async def send_reminder(self):
        raise NotImplementedError

    async def create_reminder(
        self,
        reminder: Reminder | None,
        date: datetime | None = None,
        member: discord.Member | None = None,
        transaction: Transaction | None = None,
        status: str | None = None,
    ):
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

        log.debug(f"{reminder} / {type(reminder)}")

        reminder_record = await self.storage.save_reminder(
            reminder=reminder, fields=reminder_fields
        )

        created_reminder = Reminder.from_airtable(reminder_record)

        log.info(f"Created reminder {created_reminder}")
        return created_reminder

    async def list_reminders(self):
        raise NotImplementedError

    async def remove_reminder(self):
        raise NotImplementedError
