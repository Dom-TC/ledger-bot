"""A service to provide interfacing for MemberStorage."""

import logging
from datetime import datetime, timezone
from typing import List

import requests
from currency_symbols import CurrencySymbols  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.core import Config
from ledger_bot.models import Currency
from ledger_bot.storage import CurrencyStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class CurrencyService(ServiceHelpers):
    def __init__(
        self,
        currency_storage: CurrencyStorage,
        config: Config,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.currency_storage = currency_storage
        self.config = config

        super().__init__(session_factory)

    async def get_or_add_currency(
        self,
        currency: Currency | str,
        session: AsyncSession | None = None,
    ) -> Currency:
        """Fetches an existing currency or adds a new record for it.

        Parameters
        ----------
        currency_code: Currency | str
            The Currency object or the currencies code
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Currency
            The record from the database for this Currency
        """
        async with self._get_session(session) as session:
            if isinstance(currency, Currency):
                currency_code = currency.code.upper()
            elif isinstance(currency, str):
                currency_code = currency.upper()
            else:
                log.error(
                    f"Recieved invalid currency, must be Currency or str ({currency})"
                )
                return

            currencies = await self.currency_storage.list_currencies(
                Currency.code == currency_code, session=session
            )

            if currencies:
                currency_record = currencies[0]
                log.debug(
                    f"Found currency record {currency_record.code}. Last updated: {currency_record.last_updated}"
                )
            else:
                currency_object = Currency(
                    code=currency_code,
                    symbol=CurrencySymbols.get_symbol(currency_code),
                    last_updated=datetime.now(timezone.utc),
                    bot_id=self.config.bot_id,
                )

                currency_record = await self.currency_storage.add_currency(
                    currency=currency_object, session=session
                )
                await session.commit()

            last_updated = currency_record.last_updated
            if last_updated.tzinfo is None:
                # Treat stored timestamps as UTC
                last_updated = last_updated.replace(tzinfo=timezone.utc)

            renewal_cutoff = (
                datetime.now(timezone.utc) - self.config.currency_rate_update_delta
            )

            if last_updated < renewal_cutoff or currency_record.rate is None:
                currency_record = await self.update_rate(currency=currency_record)

            return currency_record

    async def update_rate(
        self, currency: Currency, session: AsyncSession | None = None
    ) -> Currency:
        """Updates the rate for a currency.

        Uses data from https://exchangerate-api.com

        Parameters
        ----------
        currency: Currency
            The Currency object to be updated
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Currency
            The currency object including the updated rate
        """
        async with self._get_session(session) as session:
            log.info(
                f"Updating the rate for {currency.code}. Last updated {currency.last_updated}"
            )

            url = f"https://v6.exchangerate-api.com/v6/{self.config.authentication.exchangerate_api}/pair/{self.config.base_currency}/{currency.code}"
            response = requests.get(url, timeout=5)
            payload: dict = response.json()

            if payload["result"] != "success":
                log.error(
                    f"https://exchangerate-api.com returned an error: {payload["result"]}, {payload["error-type"]}"
                )
                return currency

            currency.rate = float(payload["conversion_rate"])
            currency.last_updated = datetime.now(timezone.utc)

            currency = await self.currency_storage.update_currency(
                currency,
                session=session,
                fields=["rate", "last_updated"],
            )

            log.info(f"Successfully updated rate {currency.code}@{currency.rate}")
            return currency

    async def list_all_currencies(
        self, session: AsyncSession | None = None
    ) -> List[Currency]:
        """Get a list of all currencies.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Currency]
            All the currencies in the database, empty if none exist
        """
        async with self._get_session(session) as session:
            log.info("Listing all currencies")
            currency_list = await self.currency_storage.list_currencies(session=session)

            # If no members found, return an empty list rather than None
            if not currency_list:
                currency_list = []

            log.info(f"Found {len(currency_list)} currencies")

            return currency_list
