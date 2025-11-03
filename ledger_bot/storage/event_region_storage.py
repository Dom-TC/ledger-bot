"""SQLite implementation of CurrencyStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy import case, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ledger_bot.errors import (
    CurrencyAlreadyExistsError,
    CurrencyCreationError,
    CurrencyQueryError,
)
from ledger_bot.models import EventRegion

log = logging.getLogger(__name__)


class EventRegionStorage:
    """SQLite implementation of EventRegionStorageABC."""

    async def get_region(
        self, record_id: int, session: AsyncSession
    ) -> Optional[EventRegion]:
        log.info(f"Getting EventRegion with id {record_id}")
        result: EventRegion | None = await session.get(EventRegion, record_id)
        return result

    async def list_regions(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[EventRegion]]:
        log.info(f"Listing EventRegions that match query {filters}")
        query = select(EventRegion)
        if filters:
            query = query.where(*filters)
        try:
            result = await session.execute(query)
            regions = list(result.scalars().all())
            log.info(f"Found {len(regions)} EventRegions")
            return regions if regions else None
        except SQLAlchemyError as e:
            log.exception("Database error when listing EventRegions")
            raise CurrencyQueryError("Failed to list EventRegions", e)

    async def add_region(
        self, region: EventRegion, session: AsyncSession
    ) -> EventRegion:
        try:
            session.add(region)
            await session.flush()
            await session.refresh(region)
        except IntegrityError:
            await session.rollback()
            log.debug(f"Region {region.region_name} already exists")

        return region

    async def update_region(
        self,
        region: EventRegion,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> EventRegion:
        """Update a region in the database.

        Parameters
        ----------
        region : EventRegion
            The region to update
        session : AsyncSession
            The session to be used
        fields : Optional[List[str]], optional
            The optional list of fields to update. If None, updates full model, by default None

        Returns
        -------
        EventRegion
            The updated region object.
        """
        if fields:
            # Get the existing region from the database
            db_region = await session.get(EventRegion, region.id)
            if db_region is None:
                raise ValueError(f"EventRegion with id {region.id} not found")

            # Only update the specified fields
            for field in fields:
                setattr(db_region, field, getattr(region, field))
            log.info(f"Updating region {db_region.id} fields: {fields}")
        else:
            # Full update: merge the entire object including relationships
            db_region = await session.merge(region)
            log.info(f"Updating all fields for region {db_region.id}")

        await session.flush()
        await session.refresh(db_region)

        return db_region
