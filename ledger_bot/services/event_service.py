"""A service to provide interfacing for EventStorage."""

import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from ledger_bot.core import Config
from ledger_bot.models import Event
from ledger_bot.storage import EventStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class EventService(ServiceHelpers):
    def __init__(
        self,
        event_storage: EventStorage,
        config: Config,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.event_storage = event_storage
        self.config = config

        super().__init__(session_factory)

    async def get_event(
        self, record_id: int, session: AsyncSession | None = None
    ) -> Event | None:
        """Get an event by record id.

        Parameters
        ----------
        record_id : int
            The id of the event
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[Event]
            The event object, if found
        """
        async with self._get_session(session) as session:
            event = await self.event_storage.get_event(
                record_id=record_id,
                session=session,
                options=[
                    selectinload(Event.members),
                    selectinload(Event.waitlisted_members),
                    selectinload(Event.confirmed_members),
                    selectinload(Event.hosts),
                    selectinload(Event.wines),
                    selectinload(Event.bot_messages),
                    selectinload(Event.region),
                ],
            )
            return event

    async def add_event(
        self, event: Event, session: AsyncSession | None = None
    ) -> Event:
        """Add a new event to the database.

        Parameters
        ----------
        event : Event
            The event object to add
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Event
            The event object returned from the database
        """
        async with self._get_session(session) as session:
            event_record = await self.event_storage.add_event(
                event=event, session=session
            )
            await session.commit()
            log.info(f"Added event {event_record.id} ({event_record.event_name})")
            return event_record

    async def list_all_events(self, session: AsyncSession | None = None) -> List[Event]:
        """Get a list of all events.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Event]
            All the events in the database, empty if none exist
        """
        async with self._get_session(session) as session:
            log.info("Listing all events")
            event_list = await self.event_storage.list_events(
                session=session,
                options=[
                    selectinload(Event.members),
                    selectinload(Event.waitlisted_members),
                    selectinload(Event.confirmed_members),
                    selectinload(Event.hosts),
                    selectinload(Event.wines),
                    selectinload(Event.region),
                ],
            )

            # If no events found, return an empty list rather than None
            if not event_list:
                event_list = []

            log.info(f"Found {len(event_list)} events")

            return event_list

    async def get_event_by_channel_id(
        self, channel_id: int, session: AsyncSession | None = None
    ) -> Event | None:
        """Get an event by its channel id.

        Parameters
        ----------
        channel_id : int
            The Discord channel id associated with the event
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[Event]
            The event object if found, None otherwise
        """
        async with self._get_session(session) as session:
            log.info(f"Getting event with channel_id {channel_id}")
            event_list = await self.event_storage.list_events(
                Event.channel_id == channel_id,
                session=session,
                options=[
                    selectinload(Event.members),
                    selectinload(Event.waitlisted_members),
                    selectinload(Event.confirmed_members),
                    selectinload(Event.hosts),
                    selectinload(Event.wines),
                    selectinload(Event.bot_messages),
                    selectinload(Event.region),
                ],
            )

            if event_list:
                log.info(f"Found event {event_list[0].id} with channel_id {channel_id}")
                return event_list[0]
            else:
                log.info(f"No event found with channel_id {channel_id}")
                return None

    async def list_events_by_region(
        self, region_id: int, session: AsyncSession | None = None
    ) -> List[Event]:
        """Get a list of all events for a given region.

        Parameters
        ----------
        region_id : int
            The id of the event region
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Event]
            All the events for the specified region, empty if none exist
        """
        async with self._get_session(session) as session:
            log.info(f"Listing all events for region {region_id}")
            event_list = await self.event_storage.list_events(
                Event.region_id == region_id,
                session=session,
                options=[
                    selectinload(Event.members),
                    selectinload(Event.waitlisted_members),
                    selectinload(Event.confirmed_members),
                    selectinload(Event.hosts),
                    selectinload(Event.wines),
                    selectinload(Event.region),
                ],
            )

            # If no events found, return an empty list rather than None
            if not event_list:
                event_list = []

            log.info(f"Found {len(event_list)} events for region {region_id}")

            return event_list

    async def delete_event(
        self, event: Event, session: AsyncSession | None = None
    ) -> None:
        """Delete an event from the database.

        Parameters
        ----------
        event : Event
            The event to delete
        session : AsyncSession | None, optional
            An optional session, by default None
        """
        async with self._get_session(session) as session:
            await self.event_storage.delete_event(event=event, session=session)
            await session.commit()
            log.info(f"Deleted event {event.id} ({event.event_name})")

    async def update_event(
        self,
        event: Event,
        fields: List[str] | None = None,
        session: AsyncSession | None = None,
    ) -> Event:
        """Update an event in the database.

        Parameters
        ----------
        event : Event
            The event to update
        fields : List[str] | None, optional
            If provided, only the specified fields will be updated
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Event
            The updated event object
        """
        async with self._get_session(session) as session:
            updated_event = await self.event_storage.update_event(
                event, fields=fields, session=session
            )

            await session.commit()

            log.info(f"Updated event {event.id} ({event.event_name})")
            return updated_event
