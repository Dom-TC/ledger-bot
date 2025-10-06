"""SQLite implementation of TransactionStorageABC."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.sql import ColumnElement

from ledger_bot.errors import InvalidRoleError
from ledger_bot.models import Transaction

from .abstracts import TransactionStorageABC

log = logging.getLogger(__name__)


class TransactionStorage(TransactionStorageABC):
    """SQLite implementation of TransactionStorageABC."""

    async def get_transaction(
        self,
        record_id: int,
        session: AsyncSession,
        options: Optional[List] = None,
    ) -> Optional[Transaction]:
        log.info(f"Getting transaction with record_id {record_id}")

        query = select(Transaction).where(Transaction.id == record_id)

        if options:
            query = query.options(*options)

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def add_transaction(
        self, transaction: Transaction, session: AsyncSession
    ) -> Transaction:
        log.info(
            f"Adding transaction for {transaction.wine} between {transaction.buyer_id} and {transaction.seller_id}"
        )
        session.add(transaction)
        await session.flush()
        await session.refresh(transaction)
        log.info(f"Transaction added with id {transaction.id}")
        return transaction

    async def list_transactions(
        self,
        *filters: ColumnElement[bool],
        order_by: Optional[ColumnElement] = None,
        limit: Optional[int] = None,
        options: Optional[List] = None,
        session: AsyncSession,
    ) -> Optional[List[Transaction]]:
        log.info(
            f"Listing transactions that match query {filters}, ordered by {order_by}, limited to {limit}"
        )

        query = select(Transaction)
        if filters:
            query = query.where(*filters)
        if order_by is not None:
            query = query.order_by(order_by)
        if limit is not None:
            query = query.limit(limit)
        if options:
            for opt in options:
                query = query.options(opt)

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

    async def get_count_by_status(
        self,
        member_id: int,
        role: str,  # "buyer" or "seller"
        status: str,  # "unapproved", "approved", "paid", "delivered", "complete", "cancelled", "all"
        session: AsyncSession,
    ) -> int:
        """Returns the count of transactions for a member with a given role and status."""
        if role == "buyer":
            role_column = Transaction.buyer_id
        elif role == "seller":
            role_column = Transaction.seller_id
        else:
            raise InvalidRoleError(role=role)

        # Map status to filters
        status_filters = {
            "unapproved": [
                Transaction.sale_approved.is_(False),
                Transaction.buyer_delivered.is_(False),
                Transaction.seller_delivered.is_(False),
                Transaction.buyer_paid.is_(False),
                Transaction.seller_paid.is_(False),
                Transaction.cancelled.is_(False),
            ],
            "approved": [
                Transaction.sale_approved.is_(True),
                or_(
                    Transaction.buyer_delivered.is_(False),
                    Transaction.seller_delivered.is_(False),
                ),
                or_(
                    Transaction.buyer_paid.is_(False),
                    Transaction.seller_paid.is_(False),
                ),
                Transaction.cancelled.is_(False),
            ],
            "delivered": [
                Transaction.buyer_delivered.is_(True),
                Transaction.seller_delivered.is_(True),
                Transaction.cancelled.is_(False),
            ],
            "paid": [
                Transaction.buyer_paid.is_(True),
                Transaction.seller_paid.is_(True),
                Transaction.cancelled.is_(False),
            ],
            "completed": [
                Transaction.sale_approved.is_(True),
                Transaction.buyer_delivered.is_(True),
                Transaction.seller_delivered.is_(True),
                Transaction.buyer_paid.is_(True),
                Transaction.seller_paid.is_(True),
                Transaction.cancelled.is_(False),
            ],
            "cancelled": [
                Transaction.cancelled.is_(True),
            ],
            "all": [],
        }

        if status not in status_filters:
            raise ValueError(f"Unknown status: {status}")

        # Use list_transactions with filters
        transactions = await self.list_transactions(  # type: ignore[misc]
            role_column == member_id,
            *status_filters[status],
            session=session,
        )

        log.debug(f"Returned {transactions}")
        log.debug(f"type {type(transactions)}")
        log.debug(
            f"Length {len(transactions) if isinstance(transactions, list) else 'NONE'}"
        )
        return len(transactions) if isinstance(transactions, list) else 0

    async def get_price_stats(
        self,
        member_id: int,
        role: str,  # "buyer" or "seller"
        session: AsyncSession,
        include_cancelled: bool = False,
    ) -> Tuple[float, float]:
        """Returns (total_price, avg_price) for a member's transactions."""
        log.debug(f"Getting price stats for {member_id} as {role}")

        if role == "buyer":
            role_column = Transaction.buyer_id
        elif role == "seller":
            role_column = Transaction.seller_id
        else:
            raise InvalidRoleError("role must be 'buyer' or 'seller'")

        filters = [role_column == member_id]
        if not include_cancelled:
            filters.append(Transaction.cancelled.is_(False))

        query = select(
            func.coalesce(func.sum(Transaction.price), 0),
            func.coalesce(func.avg(Transaction.price), 0),
        ).where(*filters)

        result = await session.execute(query)
        total_price, avg_price = result.one()

        return total_price, avg_price
