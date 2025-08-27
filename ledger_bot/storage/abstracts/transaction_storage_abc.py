"""The abstraction interface for transaction_storage."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Transaction


class TransactionStorageABC(ABC):
    @abstractmethod
    async def get_transaction(
        self, record_id: int, session: AsyncSession
    ) -> Optional[Transaction]:
        """Get a transaction by a record id.

        Parameters
        ----------
        record_id : int
            The id of the transaction
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[Transaction]
            The transaction object, if found.
        """
        ...

    @abstractmethod
    async def add_transaction(
        self, transaction: Transaction, session: AsyncSession
    ) -> Transaction:
        """Add a transaction to the database.

        Parameters
        ----------
        transaction : Transaction
            The transaction object to add to the database.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Transaction
            The transaction object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_transactions(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[Transaction]]:
        """List transactions that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that transactions must match.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[List[Transaction]]
            A list of transactions that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_transaction(
        self, transaction: Transaction, session: AsyncSession
    ) -> None:
        """Deletes the transaction with the given id.

        Parameters
        ----------
        transaction : Transaction
            The transaction to be deleted
        session : AsyncSession
            The session to be used
        """
        ...

    @abstractmethod
    async def update_transaction(
        self,
        transaction: Transaction,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> Transaction:
        """Update the specified fields of a transaction.

        Parameters
        ----------
        transaction : Transaction
            The transaction to update
        fields : Optional[List[str]], optional
            The optional list of filters to update.  If None, updates full model, by default None
        session : AsyncSession
            The session to be used

        Returns
        -------
        Transaction
            The updated transaction object.
        """
        ...
