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
