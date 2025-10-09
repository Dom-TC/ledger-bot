"""SQLite implementation of ReminderStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Reminder

from .abstracts import ReminderStorageABC

log = logging.getLogger(__name__)


class ReminderStorage(ReminderStorageABC):
    """SQLite implementation of MemberStorageABC."""

    async def get_reminder(
        self, record_id: int, session: AsyncSession
    ) -> Optional[Reminder]:
        log.info(f"Getting reminder with record_id {record_id}")
        result: Reminder | None = await session.get(Reminder, record_id)
        return result

    async def add_reminder(self, reminder: Reminder, session: AsyncSession) -> Reminder:
        log.info(f"Adding reminder for {reminder.member_id}")
        session.add(reminder)
        await session.flush()
        await session.refresh(reminder)
        log.info(f"Member added with id {reminder.id}")
        return reminder

    async def list_reminders(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[Reminder]]:
        log.info(f"Listing reminders that match query {filters}")
        query = select(Reminder)
        if filters:
            query = query.where(*filters)
        result = await session.execute(query)
        reminders = list(result.scalars().all())
        log.info(f"Found {len(reminders)} reminders")
        return reminders if reminders else None

    async def delete_reminder(self, reminder: Reminder, session: AsyncSession) -> None:
        log.info(
            f"Deleting reminder id {reminder.id} ({reminder.member.username} ({reminder.member.discord_id}))"
        )
        await session.delete(reminder)
        await session.flush()

    async def update_reminder(
        self,
        reminder: Reminder,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> Reminder:
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

        await session.flush()
        await session.refresh(db_reminder)
        return db_reminder
