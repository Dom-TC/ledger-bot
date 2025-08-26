"""A service to provide interfacing for ReminderStorage."""

import logging
from typing import List, Optional

from ledger_bot.models import Reminder
from ledger_bot.storage import ReminderStorage

log = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, reminder_storagee: ReminderStorage, bot_id: str):
        self.reminder_storagee = reminder_storagee
        self.bot_id = bot_id

    async def get_reminder(self, record_id: int) -> Optional[Reminder]:
        """Get a reminder with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved

        Returns
        -------
        Optional[Reminder]
            The bot_message object
        """
        reminder = await self.reminder_storagee.get_reminder(record_id=record_id)
        return reminder

    async def save_reminder(
        self, reminder: Reminder, fields: Optional[List[str]] = None
    ) -> Reminder:
        """Saves the provided Reminder.

        If it has no primary key, inserts a new instance, otherwise updates the old instance.
        If a list of fields are specified, only updates those fields.

        Paramaters
        ----------
        reminder: Reminder
            The Reminder to insert

        fields : Optional
            The fields to save / update

        Returns
        -------
        Reminder
            The saved Reminder object
        """
        log.info(f"Saving reminder for {reminder.member.username}")
        reminder.bot_id = self.bot_id

        if reminder.id:
            log.info(f"Reminder already has id {reminder.id}. Updating...")

            if fields:
                if "bot_id" not in fields:
                    fields.append("bot_id")
                log.info(f"Only updating fields: {fields}")

            reminder = await self.reminder_storagee.update_reminder(
                reminder=reminder, fields=fields
            )
        else:
            log.info("Reminder doesn't exist. Adding...")
            reminder = await self.reminder_storagee.add_reminder(reminder=reminder)

        log.info(f"Reminder saved with id {reminder.id}")
        return reminder

    async def list_all_reminders(self) -> List[Reminder]:
        """Get a list of all reminders.

        Returns
        -------
        List[Reminder]
            All the reminders in the database, empty if none exist
        """
        log.info("Listing all reminders")
        reminder_list = await self.reminder_storagee.list_reminders()

        # If no members found, return an empty list rather than None
        if not reminder_list:
            reminder_list = []

        log.info(f"Found {len(reminder_list)} reminders")

        return reminder_list

    async def delete_reminder(self, reminder: Reminder) -> None:
        """Delete the specified reminder.

        Parameters
        ----------
        reminder : Reminder
            The reminder to be deleted
        """
        log.info(f"Deleting reminder {reminder.id}")
        await self.reminder_storagee.delete_reminder(reminder)
