"""A service to provide interfacing for EventMemberStorage."""

import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from ledger_bot.core import Config
from ledger_bot.models import EventMember
from ledger_bot.storage import EventMemberStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class EventMemberService(ServiceHelpers):
    def __init__(
        self,
        event_member_storage: EventMemberStorage,
        config: Config,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.event_member_storage = event_member_storage
        self.config = config

        super().__init__(session_factory)

    async def get_event_member(
        self, record_id: int, session: AsyncSession | None = None
    ) -> EventMember | None:
        """Get an event member by record id.

        Parameters
        ----------
        record_id : int
            The id of the event member
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[EventMember]
            The event member object, if found
        """
        async with self._get_session(session) as session:
            event_member = await self.event_member_storage.get_event_member(
                record_id=record_id,
                session=session,
                options=[
                    selectinload(EventMember.event),
                    selectinload(EventMember.member),
                    selectinload(EventMember.wines),
                ],
            )
            return event_member

    async def add_event_member(
        self, event_member: EventMember, session: AsyncSession | None = None
    ) -> EventMember:
        """Add a new event member to the database.

        Parameters
        ----------
        event_member : EventMember
            The event member object to add
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        EventMember
            The event member object returned from the database
        """
        async with self._get_session(session) as session:
            event_member_record = await self.event_member_storage.add_event_member(
                event_member=event_member, session=session
            )
            await session.commit()
            log.info(
                f"Added event member {event_member_record.id} (event_id: {event_member_record.event_id}, member_id: {event_member_record.member_id})"
            )
            return event_member_record

    async def list_all_event_members(
        self, session: AsyncSession | None = None
    ) -> List[EventMember]:
        """Get a list of all event members.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[EventMember]
            All the event members in the database, empty if none exist
        """
        async with self._get_session(session) as session:
            log.info("Listing all event members")
            event_member_list = await self.event_member_storage.list_event_members(
                session=session,
                options=[
                    selectinload(EventMember.event),
                    selectinload(EventMember.member),
                    selectinload(EventMember.wines),
                ],
            )

            # If no event members found, return an empty list rather than None
            if not event_member_list:
                event_member_list = []

            log.info(f"Found {len(event_member_list)} event members")

            return event_member_list

    async def list_event_members_by_event(
        self, event_id: int, session: AsyncSession | None = None
    ) -> List[EventMember]:
        """Get a list of all event members for a given event.

        Parameters
        ----------
        event_id : int
            The id of the event
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[EventMember]
            All the event members for the specified event, empty if none exist
        """
        async with self._get_session(session) as session:
            log.info(f"Listing all event members for event {event_id}")
            event_member_list = await self.event_member_storage.list_event_members(
                EventMember.event_id == event_id,
                session=session,
                options=[
                    selectinload(EventMember.event),
                    selectinload(EventMember.member),
                    selectinload(EventMember.wines),
                ],
            )

            # If no event members found, return an empty list rather than None
            if not event_member_list:
                event_member_list = []

            log.info(
                f"Found {len(event_member_list)} event members for event {event_id}"
            )

            return event_member_list

    async def delete_event_member(
        self, event_member: EventMember, session: AsyncSession | None = None
    ) -> None:
        """Delete an event member from the database.

        Parameters
        ----------
        event_member : EventMember
            The event member to delete
        session : AsyncSession | None, optional
            An optional session, by default None
        """
        async with self._get_session(session) as session:
            await self.event_member_storage.delete_event_member(
                event_member=event_member, session=session
            )
            await session.commit()
            log.info(
                f"Deleted event member {event_member.id} (event_id: {event_member.event_id}, member_id: {event_member.member_id})"
            )

    async def update_event_member(
        self,
        event_member: EventMember,
        fields: List[str] | None = None,
        session: AsyncSession | None = None,
    ) -> EventMember:
        """Update an event member in the database.

        Parameters
        ----------
        event_member : EventMember
            The event member to update
        fields : List[str] | None, optional
            If provided, only the specified fields will be updated
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        EventMember
            The updated event member object
        """
        async with self._get_session(session) as session:
            updated_event_member = await self.event_member_storage.update_event_member(
                event_member, fields=fields, session=session
            )

            await session.commit()

            log.info(
                f"Updated event member {event_member.id} (event_id: {event_member.event_id}, member_id: {event_member.member_id})"
            )
            return updated_event_member
