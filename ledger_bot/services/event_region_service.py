"""A service to provide interfacing for MemberStorage."""

import logging
from typing import List

from asyncache import cached
from cachetools import LRUCache
from discord.app_commands import Choice
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.core import Config
from ledger_bot.models import EventRegion
from ledger_bot.storage import EventRegionStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class EventRegionService(ServiceHelpers):
    _list_all_regions_cache: LRUCache = LRUCache(maxsize=64)

    def __init__(
        self,
        event_region_storage: EventRegionStorage,
        config: Config,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.event_region_storage = event_region_storage
        self.config = config

        super().__init__(session_factory)

    async def get_region(
        self, record_id: int, session: AsyncSession | None = None
    ) -> EventRegion | None:
        """Get a EventRegion with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[EventRegion]
            The EventRegion object
        """
        async with self._get_session(session) as session:
            reminder = await self.event_region_storage.get_region(
                record_id=record_id, session=session
            )
            return reminder

    @cached(_list_all_regions_cache)
    async def list_all_regions(
        self, session: AsyncSession | None = None
    ) -> List[EventRegion]:
        """Get a list of all EventRegions.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[EventRegion]
            All the EventRegions in the database, empty if none exist
        """
        async with self._get_session(session) as session:
            log.info("Listing all EventRegion")
            region_list = await self.event_region_storage.list_regions(session=session)

            if not region_list:
                region_list = []

            log.info(f"Found {len(region_list)} EventRegions")

            return region_list

    async def get_region_choices(
        self, session: AsyncSession | None = None
    ) -> List[Choice[int]]:
        """Get a list of Choices for all EventRegions.

        This is used for discord.py app_commands.choices decorator.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Choice[int]]
            A list of Choice objects with name=region_name and value=id
        """
        regions = await self.list_all_regions(session=session)
        return [Choice(name=region.region_name, value=region.id) for region in regions]

    async def add_region(
        self,
        region: EventRegion,
        session: AsyncSession | None = None,
    ) -> EventRegion:
        """Saves the provided EventRegion.

        Paramaters
        ----------
        region: EventRegion
            The EventRegion to insert

        Returns
        -------
        EventRegion
            The saved EventRegion object
        """
        log.info(f"Saving region {region.region_name}")
        region.bot_id = self.config.bot_id

        async with self._get_session(session) as session:
            if region.id:
                log.info(f"EventRegion already has id {region.id}. Skipping...")
                return region
            else:
                region = await self.event_region_storage.add_region(
                    region=region, session=session
                )
                await session.commit()

            if region.id:
                log.debug(f"EventRegion saved with id {region.id}")
                self._list_all_regions_cache.clear()
            return region

    async def add_or_update_region(
        self,
        region: EventRegion,
        session: AsyncSession | None = None,
    ) -> EventRegion:
        """Add a new region or update an existing one by region_name.

        If a region with the same region_name exists, update it with the new data.
        Otherwise, add it as a new region.

        Parameters
        ----------
        region : EventRegion
            The region to add or update
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        EventRegion
            The added or updated region
        """
        log.info(f"Adding or updating region {region.region_name}")
        region.bot_id = self.config.bot_id

        async with self._get_session(session) as session:
            # Check if a region with this name already exists
            regions = await self.event_region_storage.list_regions(
                EventRegion.region_name == region.region_name, session=session
            )

            if regions and len(regions) > 0:
                existing_region = regions[0]
                log.info(
                    f"Region {region.region_name} exists with id {existing_region.id}, updating it"
                )
                # Update the existing region's fields
                existing_region.new_event_category = region.new_event_category
                existing_region.event_signup_channel = region.event_signup_channel
                existing_region.bot_id = region.bot_id

                updated_region = await self.event_region_storage.update_region(
                    region=existing_region, session=session
                )
                await session.commit()
                self._list_all_regions_cache.clear()
                return updated_region
            else:
                log.info(f"Region {region.region_name} does not exist, adding it")
                # Add as a new region
                region = await self.event_region_storage.add_region(
                    region=region, session=session
                )
                await session.commit()
                self._list_all_regions_cache.clear()
                return region
