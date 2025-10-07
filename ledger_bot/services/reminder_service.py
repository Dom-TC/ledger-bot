"""A service to provide interfacing for ReminderStorage."""

import logging
from typing import AsyncGenerator, List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.models import Reminder
from ledger_bot.storage import ReminderStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class ReminderService(ServiceHelpers):
    def __init__(
        self,
        reminder_storagee: ReminderStorage,
        bot_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.reminder_storagee = reminder_storagee
        self.bot_id = bot_id

        super().__init__(session_factory)

    async def get_reminder(
        self, record_id: int, session: AsyncSession | None = None
    ) -> Reminder | None:
        """Get a reminder with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[Reminder]
            The bot_message object
        """
        async with self._get_session(session) as session:
            reminder = await self.reminder_storagee.get_reminder(
                record_id=record_id, session=session
            )
            return reminder

    async def save_reminder(
        self,
        reminder: Reminder,
        fields: List[str] | None = None,
        session: AsyncSession | None = None,
    ) -> Reminder:
        """Saves the provided Reminder.

        If it has no primary key, inserts a new instance, otherwise updates the old instance.
        If a list of fields are specified, only updates those fields.

        Paramaters
        ----------
        reminder: Reminder
            The Reminder to insert
        session : AsyncSession | None, optional
            An optional session, by default None

        fields : Optional
            The fields to save / update

        Returns
        -------
        Reminder
            The saved Reminder object
        """
        async with self._get_session(session) as session:
            log.debug(f"reminder: {reminder}")

            log.info(f"Saving reminder for member with id{reminder.member_id}")
            reminder.bot_id = self.bot_id

            if reminder.id:
                log.info(f"Reminder already has id {reminder.id}. Updating...")

                if fields:
                    if "bot_id" not in fields:
                        fields.append("bot_id")
                    log.info(f"Only updating fields: {fields}")

                reminder = await self.reminder_storagee.update_reminder(
                    reminder=reminder, fields=fields, session=session
                )
                await session.commit()
            else:
                log.info("Reminder doesn't exist. Adding...")
                reminder = await self.reminder_storagee.add_reminder(
                    reminder=reminder, session=session
                )
                await session.commit()

            log.info(f"Reminder saved with id {reminder.id}")
            return reminder

    async def list_all_reminders(
        self, session: AsyncSession | None = None
    ) -> List[Reminder]:
        """Get a list of all reminders.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Reminder]
            All the reminders in the database, empty if none exist
        """
        log.info("Listing all reminders")
        async with self._get_session(session) as session:
            reminder_list = await self.reminder_storagee.list_reminders(session=session)

        # If no members found, return an empty list rather than None
        if not reminder_list:
            reminder_list = []

        log.info(f"Found {len(reminder_list)} reminders")

        return reminder_list

    async def delete_reminder(
        self, reminder: Reminder, session: AsyncSession | None = None
    ) -> None:
        """Delete the specified reminder.

        Parameters
        ----------
        reminder : Reminder
            The reminder to be deleted
        session : AsyncSession | None, optional
            An optional session, by default None
        """
        log.info(f"Deleting reminder {reminder.id}")
        async with self._get_session(session) as session:
            await self.reminder_storagee.delete_reminder(reminder, session=session)
            await session.commit()
