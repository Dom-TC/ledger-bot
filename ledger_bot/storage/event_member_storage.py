"""SQLite implementation of EventMember storage."""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ledger_bot.errors import (
    EventMemberAlreadyExistsError,
    EventMemberCreationError,
    EventMemberQueryError,
)
from ledger_bot.models import EventMember

log = logging.getLogger(__name__)


class EventMemberStorage:
    """SQLite implementation of EventMember storage."""

    async def get_event_member(
        self, record_id: int, session: AsyncSession, options: Optional[List] = None
    ) -> Optional[EventMember]:
        """Get an event member by record id.

        Parameters
        ----------
        record_id : int
            The id of the event member
        session : AsyncSession
            The session to be used
        options : Optional[List], optional
            Optional SQLAlchemy query options for eager loading, by default None

        Returns
        -------
        Optional[EventMember]
            The event member object, if found.
        """
        log.info(f"Getting event member with record_id {record_id}")
        query = select(EventMember).where(EventMember.id == record_id)

        if options:
            query = query.options(*options)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def add_event_member(
        self, event_member: EventMember, session: AsyncSession
    ) -> EventMember:
        """Add an event member to the database.

        Parameters
        ----------
        event_member : EventMember
            The event member object to add to the database.
        session : AsyncSession
            The session to be used

        Returns
        -------
        EventMember
            The event member object returned from the database.
        """
        log.info(
            f"Adding event member for event_id {event_member.event_id}, member_id {event_member.member_id}"
        )
        session.add(event_member)
        try:
            await session.flush()
            await session.refresh(event_member)
            log.info(f"Event member added with id {event_member.id}")
            return event_member

        except IntegrityError as e:
            log.exception(
                f"Adding event member for event_id {event_member.event_id}, member_id {event_member.member_id} raised an IntegrityError"
            )
            await session.rollback()
            raise EventMemberAlreadyExistsError(event_member, e)
        except SQLAlchemyError as e:
            log.exception(
                f"Adding event member for event_id {event_member.event_id}, member_id {event_member.member_id} raised an SQLAlchemyError"
            )
            await session.rollback()
            raise EventMemberCreationError(event_member, e)

    async def list_event_members(
        self,
        *filters: ColumnElement[bool],
        session: AsyncSession,
        options: Optional[List] = None,
    ) -> Optional[List[EventMember]]:
        """List event members that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that event members must match.
        session : AsyncSession
            The session to be used
        options : Optional[List], optional
            Optional SQLAlchemy query options for eager loading, by default None

        Returns
        -------
        Optional[List[EventMember]]
            A list of event members that matched the supplied filter, if any.
        """
        log.info(f"Listing event members that match query {filters}")
        query = select(EventMember)
        if filters:
            query = query.where(*filters)
        if options:
            query = query.options(*options)
        try:
            result = await session.execute(query)
            event_members = list(result.scalars().all())
            log.info(f"Found {len(event_members)} event members")
            return event_members if event_members else None
        except SQLAlchemyError as e:
            log.exception("Database error when listing event members")
            raise EventMemberQueryError("Failed to list event members", e)

    async def delete_event_member(
        self, event_member: EventMember, session: AsyncSession
    ) -> None:
        """Delete an event member from the database.

        Parameters
        ----------
        event_member : EventMember
            The event member to be deleted
        session : AsyncSession
            The session to be used
        """
        log.info(
            f"Deleting event member id {event_member.id} (event_id: {event_member.event_id}, member_id: {event_member.member_id})"
        )
        await session.delete(event_member)
        await session.flush()

    async def update_event_member(
        self,
        event_member: EventMember,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> EventMember:
        """Update an event member in the database.

        Parameters
        ----------
        event_member : EventMember
            The event member to update
        session : AsyncSession
            The session to be used
        fields : Optional[List[str]], optional
            The optional list of fields to update. If None, updates full model, by default None

        Returns
        -------
        EventMember
            The updated event member object.
        """
        # Attach the event member object to the session
        db_event_member: EventMember = await session.merge(event_member)

        if fields:
            # Only update the specified fields
            for field in fields:
                setattr(db_event_member, field, getattr(event_member, field))
            log.info(f"Updating event member {db_event_member.id} fields: {fields}")
        else:
            # Full update: merge already updates all fields
            log.info(f"Updating all fields for event member {db_event_member.id}")

        await session.flush()
        await session.refresh(db_event_member)
        return db_event_member
