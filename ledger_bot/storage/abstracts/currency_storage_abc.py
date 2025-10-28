"""The abstraction interface for currencies."""

from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Currency


class CurrencyStorageABC(ABC):
    @abstractmethod
    async def get_currency(
        self, currency_code: str, session: AsyncSession
    ) -> Optional[Currency]:
        """Get a member by its code.

        Parameters
        ----------
        currency_code : str
            The code of the currency
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[Member]
            The member object, if found.
        """
        ...

    @abstractmethod
    async def add_currency(self, currency: Currency, session: AsyncSession) -> Currency:
        """Add a currency to the database.

        Parameters
        ----------
        currency : currency
            The currency object to add to the database.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Currency
            The currency object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_currencies(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[Currency]]:
        """List currencies that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that members must match.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[List[Currency]]
            A list of currencies that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_currency(self, currency: Currency, session: AsyncSession) -> None:
        """Deletes the currency.

        Parameters
        ----------
        currency : Currency
            The currency to be deleted
        session : AsyncSession
            The session to be used
        """
        ...

    @abstractmethod
    async def update_currency(
        self,
        currency: Currency,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> Currency:
        """Update the specified fields of a currency.

        Parameters
        ----------
        currency : Currency
            The currency to update
        fields : Optional[List[str]], optional
            The optional list of filters to update.  If None, updates full model, by default None
        session : AsyncSession
            The session to be used

        Returns
        -------
        Currency
            The updated currency object.
        """
        ...
