"""SQLite implementation of TransactionStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Transaction

from .abstracts import TransactionStorageABC

log = logging.getLogger(__name__)


class TransactionStorage(TransactionStorageABC):
    """SQLite implementation of TransactionStorageABC."""

    async def get_transaction(
        self, record_id: int, session: AsyncSession
    ) -> Optional[Transaction]:
        log.info(f"Getting transaction with record_id {record_id}")
        result: Transaction | None = await session.get(Transaction, record_id)
        return result

    async def add_transaction(
        self, transaction: Transaction, session: AsyncSession
    ) -> Transaction:
        log.info(
            f"Adding transaction for {transaction.wine} between {transaction.buyer.username} and {transaction.seller.username}"
        )
        session.add(transaction)
        await session.flush()
        await session.refresh(transaction)
        log.info(f"Transaction added with id {transaction.id}")
        return transaction

    async def list_transactions(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[Transaction]]:
        log.info(f"Listing transactions that match query {filters}")
        query = select(Transaction)
        if filters:
            query = query.where(*filters)
        result = await session.execute(query)
        transactions = list(result.scalars().all())
        log.info(f"Found {len(transactions)} transactions")
        return transactions if transactions else None

    async def delete_transaction(
        self, transaction: Transaction, session: AsyncSession
    ) -> None:
        log.info(
            f"Deleting transaction with id {transaction.id} ({transaction.wine} between {transaction.buyer.username} and {transaction.seller.username})"
        )
        await session.delete(transaction)
        await session.flush()

    async def update_transaction(
        self,
        transaction: Transaction,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> Transaction:
        # Attach the transaction object to the session
        db_transaction: Transaction = await session.merge(transaction)

        if fields:
            # Only update the specified fields
            for field in fields:
                setattr(db_transaction, field, getattr(transaction, field))
            log.info(f"Updating transaction {db_transaction.id} fields: {fields}")
        else:
            # Full update: merge already updates all fields
            log.info(f"Updating all fields for transaction {db_transaction.id}")

        await session.flush()
        await session.refresh(db_transaction)
        return db_transaction
