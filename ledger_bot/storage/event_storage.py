"""SQLite implementation of Event storage."""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ledger_bot.errors import (
    EventAlreadyExistsError,
    EventCreationError,
    EventQueryError,
)
from ledger_bot.models import Event

log = logging.getLogger(__name__)


class EventStorage:
    """SQLite implementation of Event storage."""

    async def get_event(
        self, record_id: int, session: AsyncSession, options: Optional[List] = None
    ) -> Optional[Event]:
        """Get an event by record id.

        Parameters
        ----------
        record_id : int
            The id of the event
        session : AsyncSession
            The session to be used
        options : Optional[List], optional
            Optional SQLAlchemy query options for eager loading, by default None

        Returns
        -------
        Optional[Event]
            The event object, if found.
        """
        log.info(f"Getting event with record_id {record_id}")
        query = select(Event).where(Event.id == record_id)

        if options:
            query = query.options(*options)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def add_event(self, event: Event, session: AsyncSession) -> Event:
        """Add an event to the database.

        Parameters
        ----------
        event : Event
            The event object to add to the database.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Event
            The event object returned from the database.
        """
        log.info(f"Adding event {event.event_name}")
        session.add(event)
        try:
            await session.flush()
            await session.refresh(event)
            log.info(f"Event added with id {event.id}")
            return event

        except IntegrityError as e:
            log.exception(f"Adding event {event.event_name} raised an IntegrityError")
            await session.rollback()
            raise EventAlreadyExistsError(event, e)
        except SQLAlchemyError as e:
            log.exception(f"Adding event {event.event_name} raised an SQLAlchemyError")
            await session.rollback()
            raise EventCreationError(event, e)

    async def list_events(
        self,
        *filters: ColumnElement[bool],
        session: AsyncSession,
        options: Optional[List] = None,
    ) -> Optional[List[Event]]:
        """List events that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that events must match.
        session : AsyncSession
            The session to be used
        options : Optional[List], optional
            Optional SQLAlchemy query options for eager loading, by default None

        Returns
        -------
        Optional[List[Event]]
            A list of events that matched the supplied filter, if any.
        """
        log.info(f"Listing events that match query {filters}")
        query = select(Event)
        if filters:
            query = query.where(*filters)
        if options:
            query = query.options(*options)
        try:
            result = await session.execute(query)
            events = list(result.scalars().all())
            log.info(f"Found {len(events)} events")
            return events if events else None
        except SQLAlchemyError as e:
            log.exception("Database error when listing events")
            raise EventQueryError("Failed to list events", e)

    async def delete_event(self, event: Event, session: AsyncSession) -> None:
        """Delete an event from the database.

        Parameters
        ----------
        event : Event
            The event to be deleted
        session : AsyncSession
            The session to be used
        """
        log.info(f"Deleting event id {event.id} ({event.event_name})")
        await session.delete(event)
        await session.flush()

    async def update_event(
        self, event: Event, session: AsyncSession, fields: Optional[List[str]] = None
    ) -> Event:
        """Update an event in the database.

        Parameters
        ----------
        event : Event
            The event to update
        session : AsyncSession
            The session to be used
        fields : Optional[List[str]], optional
            The optional list of fields to update. If None, updates full model, by default None

        Returns
        -------
        Event
            The updated event object.
        """
        # Attach the event object to the session
        db_event: Event = await session.merge(event)

        if fields:
            # Only update the specified fields
            for field in fields:
                setattr(db_event, field, getattr(event, field))
            log.info(f"Updating event {db_event.id} fields: {fields}")
        else:
            # Full update: merge already updates all fields
            log.info(f"Updating all fields for event {db_event.id}")

        await session.flush()
        await session.refresh(db_event)
        return db_event
