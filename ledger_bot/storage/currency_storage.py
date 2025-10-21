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
from ledger_bot.models import Currency

from .abstracts import CurrencyStorageABC

log = logging.getLogger(__name__)


class CurrencyStorage(CurrencyStorageABC):
    """SQLite implementation of CurrencyStorageABC."""

    async def get_currency(
        self, currency_code: str, session: AsyncSession
    ) -> Optional[Currency]:
        log.info(f"Getting currency with code {currency_code}")
        result: Currency | None = await session.get(Currency, currency_code)
        return result

    async def add_currency(self, currency: Currency, session: AsyncSession) -> Currency:
        log.info(f"Adding currency {currency.code}")
        session.add(currency)
        try:
            await session.flush()
            await session.refresh(currency)
            log.info(f"Currency added with id {currency.code}")
            return currency

        except IntegrityError as e:
            log.exception(f"Adding currency {currency.code} raised an IntegrityError")
            await session.rollback()
            raise CurrencyAlreadyExistsError(currency, e)
        except SQLAlchemyError as e:
            log.exception(f"Adding curremcy {currency.code} raised an SQLAlchemyError")
            await session.rollback()
            raise CurrencyCreationError(currency, e)

    async def list_currencies(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[Currency]]:
        log.info(f"Listing currencies that match query {filters}")
        query = select(Currency)
        if filters:
            query = query.where(*filters)
        try:
            result = await session.execute(query)
            currency = list(result.scalars().all())
            log.info(f"Found {len(currency)} currencies")
            return currency if currency else None
        except SQLAlchemyError as e:
            log.exception("Database error when listing currencies")
            raise CurrencyQueryError("Failed to list currencies", e)

    async def delete_currency(self, currency: Currency, session: AsyncSession) -> None:
        log.info(f"Deleting currency {currency.code}")
        await session.delete(currency)
        await session.flush()

    async def update_currency(
        self,
        currency: Currency,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> Currency:
        # Attach the currency object to the session
        db_currency: Currency = await session.merge(currency)

        if fields:
            # Only update the specified fields
            for field in fields:
                setattr(db_currency, field, getattr(currency, field))
            log.info(f"Updating currency {db_currency.code} fields: {fields}")
        else:
            # Full update: merge already updates all fields
            log.info(f"Updating all fields for currency {db_currency.code}")

        await session.flush()
        await session.commit()
        await session.refresh(db_currency)
        return db_currency
