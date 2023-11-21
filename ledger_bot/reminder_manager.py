"""Classing for managing Reminders."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import discord
from apscheduler import events
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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

        initial_refresh_run = datetime.now() + timedelta(seconds=5)
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
                name=f"Reminder: {reminder.notes.strip()} now ({reminder.date})!",
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

    async def send_reminder():
        pass
