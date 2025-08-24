"""The abstraction interface for reminder_storage."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Reminder


class ReminderStorageABC(ABC):
    @abstractmethod
    async def get_reminder(self, record_id: int) -> Optional[Reminder]:
        """Get a reminder by a record id.

        Parameters
        ----------
        record_id : int
            The id of the reminder

        Returns
        -------
        Optional[Reminder]
            The reminder object, if found.
        """
        ...

    @abstractmethod
    async def add_reminder(self, reminder: Reminder) -> Reminder:
        """Add a reminder to the database.

        Parameters
        ----------
        reminder : Reminder
            The reminder object to add to the database.

        Returns
        -------
        Reminder
            The reminder object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_reminders(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[Reminder]]:
        """List reminders that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that reminders must match.

        Returns
        -------
        Optional[List[Reminder]]
            A list of reminders that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_reminder(self, reminder: Reminder) -> None:
        """Deletes the reminder with the given id.

        Parameters
        ----------
        reminder : Reminder
            The reminder to be deleted
        """
        ...

    @abstractmethod
    async def update_reminder(
        self, reminder: Reminder, fields: Optional[List[str]] = None
    ) -> Reminder:
        """Update the specified fields of a reminder.

        Parameters
        ----------
        reminder : Reminder
            The reminder to update
        fields : Optional[List[str]], optional
            The optional list of filters to update.  If None, updates full model, by default None

        Returns
        -------
        Reminder
            The updated reminder object.
        """
        ...
