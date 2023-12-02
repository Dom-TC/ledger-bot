"""Mixin for dealing with the Reminders table."""

import logging
from typing import AsyncGenerator, Optional

from aiohttp import ClientSession

from ledger_bot.models import Reminder

from .base_storage import BaseStorage

log = logging.getLogger(__name__)


class RemindersMixin(BaseStorage):
    reminders_url: str
    bot_id: str

    def _list_all_reminders(
        self,
        filter_by_formula: Optional[str],
        sort: Optional[list[str]] = None,
        session: Optional[ClientSession] = None,
    ) -> AsyncGenerator[dict, None]:
        return self._iterate(
            self.reminders_url,
            filter_by_formula=filter_by_formula,
            sort=sort,
            session=session,
        )

    async def retrieve_reminders(self) -> AsyncGenerator[Reminder, None]:
        reminders_iterator = self._list_all_reminders(filter_by_formula=None)
        async for reminder in reminders_iterator:
            yield Reminder.from_airtable(reminder)

    async def retrieve_reminder(self, key: str) -> Reminder:
        result = await self._get(f"{self.reminders_url}/{key}")
        return Reminder.from_airtable(result)

    async def insert_reminder(
        self, record: dict, session: Optional[ClientSession] = None
    ) -> dict:
        """
        Inserts a member into the table.

        Paramaters
        ----------
        record : dict
            The record to insert

        session : ClientSession, optional
            The ClientSession to use

        Returns
        -------
        dict
            A Dictionary containing the inserted record
        """
        return await self._insert(self.reminders_url, record, session)

    async def update_reminder(
        self,
        record_id: str,
        reminder_record: dict,
        session: Optional[ClientSession] = None,
    ) -> dict:
        """
        Updates a specific reminder record.

        Paramaters
        ----------
        record_id : str
            The primary key of the reminder to update

        reminder_record : dict
            The records to update

        session : ClientSession, optional
            The ClientSession to use

        """
        return await self._update(
            self.reminders_url + "/" + record_id, reminder_record, session
        )

    async def save_reminder(self, reminder: Reminder, fields=None) -> dict:
        """
        Saves a reminder.

        If it has no primary key, inserts a new instance, otherwise updates the old instance.
        If a list of fields are specified, only saves/updates those fields.

        Paramaters
        ----------
        reminder : Reminder
            The reminder to insert

        fields : Optional
            The fields to save / update

        """
        fields = fields or [
            "date",
            "member_id",
            "transaction_id",
            "status",
        ]

        # Always store bot_id
        reminder.bot_id = self.bot_id or ""
        if "bot_id" not in fields:
            fields.append("bot_id")

        log.debug(f"{reminder} / {type(reminder)}")

        reminder_data = reminder.to_airtable(fields=fields)
        log.info(f"Adding reminder data: {reminder_data['fields']}")
        if reminder.record_id:
            log.info(f"Updating reminder with id: {reminder_data['id']}")
            return await self.update_reminder(
                reminder_data["id"], reminder_data["fields"]
            )
        else:
            log.info("Adding reminder to Airtable")
            return await self.insert_reminder(reminder_data["fields"])

    async def remove_reminder(self, *reminder_ids: str):
        log.debug(f"Deleting reminders: {reminder_ids}")
        await self._delete(self.reminders_url, list(reminder_ids))
        log.debug(f"Deleted reminders: {reminder_ids}")
