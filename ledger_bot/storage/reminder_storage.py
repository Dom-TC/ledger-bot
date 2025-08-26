"""SQLite implementation of ReminderStorageABC."""

import logging
from typing import AsyncGenerator, List, Optional

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Reminder

from .abstracts import ReminderStorageABC

log = logging.getLogger(__name__)


class ReminderStorage(ReminderStorageABC):
    """SQLite implementation of MemberStorageABC."""

    def __init__(self, session_factory: async_sessionmaker):
        """Initialise ReminderStorage.

        Parameters
        ----------
        session_factory : Callable[[], AsyncSession]
            Factory to produce new SQLAlchemy AsyncSession objects.
        """
        self._session_factory = session_factory

    async def get_reminder(self, record_id: int) -> Optional[Reminder]:
        async with self._session_factory() as session:
            log.info(f"Getting reminder with record_id {record_id}")
            result: Reminder | None = await session.get(Reminder, record_id)
            return result

    async def add_reminder(self, reminder: Reminder) -> Reminder:
        async with self._session_factory() as session:
            log.info(f"Adding reminder for {reminder.member.username}")
            session.add(reminder)
            await session.commit()
            await session.refresh(reminder)
            log.info(f"Member added with id {reminder.id}")
            return reminder

    async def list_reminders(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[Reminder]]:
        async with self._session_factory() as session:
            log.info(f"Listing reminders that match query {filters}")
            query = select(Reminder)
            if filters:
                query = query.where(*filters)
            result = await session.execute(query)
            reminders = result.scalars().all()
            log.info(f"Found {len(reminders)} reminders")
            return reminders if reminders else None

    async def delete_reminder(self, reminder: Reminder) -> None:
        async with self._session_factory() as session:
            log.info(
                f"Deleting reminder id {reminder.id} ({reminder.member.username} ({reminder.member.discord_id}))"
            )
            await session.delete(reminder)
            await session.commit()

    async def update_reminder(
        self, reminder: Reminder, fields: Optional[List[str]] = None
    ) -> Reminder:
        async with self._session_factory() as session:
            # Attach the reminder object to the session
            db_reminder: Reminder = await session.merge(reminder)

            if fields:
                # Only update the specified fields
                for field in fields:
                    setattr(db_reminder, field, getattr(reminder, field))
                log.info(f"Updating reminder {db_reminder.id} fields: {fields}")
            else:
                # Full update: merge already updates all fields
                log.info(f"Updating all fields for reminder {db_reminder.id}")

            await session.commit()
            await session.refresh(db_reminder)
            return db_reminder
