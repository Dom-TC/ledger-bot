"""A service to provide interfacing for TransactionStorage."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List

from asyncache import cached
from cachetools import LRUCache
from discord import Member as DiscordMember
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.errors import (
    TransactionApprovedError,
    TransactionCancelledError,
    TransactionInvalidBuyerError,
    TransactionInvalidMemberError,
    TransactionServiceError,
)
from ledger_bot.models import Transaction
from ledger_bot.storage import TransactionStorage

from .bot_message_service import BotMessageService
from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class TransactionService(ServiceHelpers):
    def __init__(
        self,
        transaction_storage: TransactionStorage,
        bot_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.transaction_storage = transaction_storage
        self.bot_id = bot_id

        super().__init__(session_factory)

    async def get_transaction(
        self, record_id: int, session: AsyncSession | None = None
    ) -> Transaction | None:
        """Get a transaction with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[Transaction]
            The transaction object
        """
        async with self._get_session(session) as session:
            transaction = await self.transaction_storage.get_transaction(
                record_id=record_id, session=session
            )
            return transaction

    async def get_completed_transaction(
        self, hours_completed: int = 0, session: AsyncSession | None = None
    ) -> List[Transaction]:
        """Get a list of transactions that are completed.

        A transaction is considered completed when:
          sale_approved,
          buyer_marked_delivered,
          seller_marked_delivered,
          buyer_marked_paid,
          seller_marked_paid
        are all true, and:
          cancelled
        is false

        Parameters
        ----------
        hours_completed : int, optional
            The minumum number of hours ago a transaction must have been completed for it to be included, by default 0
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Transaction]
            A list of transactions
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_completed)

        log.info(f"Finding all completed transactions before {cutoff}")
        filter_ = and_(
            Transaction.sale_approved == 1,
            Transaction.buyer_paid == 1,
            Transaction.seller_delivered == 1,
            Transaction.buyer_paid == 1,
            Transaction.seller_delivered == 1,
            Transaction.cancelled == 0,
            Transaction.creation_date < cutoff,
            Transaction.approved_date < cutoff,
            Transaction.delivered_date < cutoff,
            Transaction.paid_date < cutoff,
        )

        async with self._get_session(session) as session:
            completed_transactions = await self.transaction_storage.list_transactions(
                filter_, session=session
            )

            return completed_transactions or []

    async def save_transaction(
        self,
        transaction: Transaction,
        fields: List[str] | None = None,
        session: AsyncSession | None = None,
    ) -> Transaction:
        """Saves the provided Transaction.

        If it has no primary key, inserts a new instance, otherwise updates the old instance.
        If a list of fields are specified, only saves/updates those fields.

        Paramaters
        ----------
        transaction : Transaction
            The transaction to insert
        session : AsyncSession | None, optional
            An optional session, by default None

        fields : Optional
            The fields to save / update

        Returns
        -------
        Transaction
            The transaction object
        """
        log.debug(transaction)
        log.info(f"Saving transaction for {transaction.wine}")
        transaction.bot_id = self.bot_id

        async with self._get_session(session) as session:
            if transaction.id:
                log.info(f"Transaction already has id {transaction.id}. Updating...")

                if fields:
                    if "bot_id" not in fields:
                        fields.append("bot_id")
                    log.info(f"Only updating fields: {fields}")

                transaction = await self.transaction_storage.update_transaction(
                    transaction=transaction, fields=fields, session=session
                )
            else:
                log.info("Transaction doesn't exist. Adding...")
                transaction = await self.transaction_storage.add_transaction(
                    transaction=transaction, session=session
                )

            await session.commit()
            await session.refresh(transaction)
            log.info(f"Transaction saved with id {transaction.id}")
            return transaction

    async def list_all_transactions(
        self, session: AsyncSession | None = None
    ) -> List[Transaction]:
        """Get a list of all transactions.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Transaction]
            All the transactions in the database, empty if none exist
        """
        log.info("Listing all transactions")
        async with self._get_session(session) as session:
            transaction_list = await self.transaction_storage.list_transactions(
                session=session
            )

            # If no members found, return an empty list rather than None
            if not transaction_list:
                transaction_list = []

            log.info(f"Found {len(transaction_list)} transactions")

            return transaction_list

    async def delete_transaction(
        self, transaction: Transaction, session: AsyncSession | None = None
    ) -> None:
        """Delete the specified transaction.

        Parameters
        ----------
        transaction : Transaction
            The transaction to be deleted
        session : AsyncSession | None, optional
            An optional session, by default None
        """
        log.info(f"Deleting transaction {transaction.id}")
        async with self._get_session(session) as session:
            await self.transaction_storage.delete_transaction(
                transaction, session=session
            )

    async def approve_transaction(
        self,
        transaction: Transaction,
        reactor: DiscordMember,
        session: AsyncSession | None = None,
    ) -> Transaction:
        """Approve the specified transaction.

        Parameters
        ----------
        transaction : Transaction
            The transaction to be approved
        reactor : DiscordMember
            The member who made the reaction
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Transaction
            The approved transaction

        Raises
        ------
        TransactionCancelledError
            The transaction was already cancelled
        TransactionInvalidBuyerError
            The specified buyer doesn't match the transaction buyer
        """
        async with self._get_session(session) as session:
            if transaction.id is None:
                log.exception("Transaction has no id. Ignoring")
                raise TransactionServiceError

            refreshed_transaction = await self.get_transaction(
                transaction.id, session=session
            )

            if refreshed_transaction is None:
                log.exception("Refreshed transaction returned None")
                raise TransactionServiceError

            transaction = refreshed_transaction

            log.info(f"Approving transaction {transaction.id}")

            if transaction.cancelled:
                log.info(
                    f"Ignoring approval from {reactor.name} on {transaction.id} - Transaction cancelled."
                )
                raise TransactionCancelledError(transaction=transaction)

            await session.refresh(transaction, attribute_names=["buyer", "seller"])

            if reactor.id != transaction.buyer.discord_id:
                log.info(
                    f"Ignoring approval from {reactor.name} on {transaction.id} - Reactor is not the buyer."
                )
                raise TransactionInvalidBuyerError(
                    transaction=transaction, member=reactor
                )

            transaction.sale_approved = True
            transaction.approved_date = datetime.now(timezone.utc)
            fields = ["sale_approved", "approved_date"]
            log.debug(f"transaction: {transaction}")

            saved_transaction = await self.save_transaction(
                transaction=transaction, fields=fields, session=session
            )

            await session.refresh(transaction, attribute_names=["buyer", "seller"])
            return saved_transaction

    async def cancel_transaction(
        self,
        transaction: Transaction,
        reactor: DiscordMember,
        session: AsyncSession | None = None,
    ) -> Transaction:
        """Cancel the specified transaction.

        Parameters
        ----------
        transaction : Transaction
            The transaction to be cancelled
        reactor : DiscordMember
            The member who made the reaction
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Transaction
            The cancelled transaction

        Raises
        ------
        TransactionApprovedError
            The transaction was already approved
        TransactionInvalidMemberError
            The member wasn't involved in the transaction
        """
        log.info(f"Cancelling transaction {transaction.id}")

        if transaction.sale_approved:
            log.info(
                f"Ignoring cancellation of {transaction.id}. Transaction already approved."
            )
            raise TransactionApprovedError(transaction=transaction)

        if (reactor.id != transaction.buyer_id) and (
            reactor.id != transaction.seller_id
        ):
            log.info(f"Ignoring cancellation of {transaction.id} from invalid member")
            raise TransactionInvalidMemberError(transaction=transaction, member=reactor)

        transaction.cancelled = True
        transaction.cancelled_date = datetime.now(timezone.utc)
        fields = ["cancelled", "cancelled_date"]
        log.debug(f"transaction: {transaction}")

        return await self.save_transaction(
            transaction=transaction, fields=fields, session=session
        )

    async def mark_transaction_delivered(
        self,
        transaction: Transaction,
        reactor: DiscordMember,
        session: AsyncSession | None = None,
    ) -> Transaction:
        """Mark the transaction as delivered.

        Parameters
        ----------
        transaction : Transaction
            The transaction to be updated
        reactor : DiscordMember
            The member who made the reaction
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Transaction
            The updated transaction

        Raises
        ------
        TransactionCancelledError
            The transaction was already cancelled
        TransactionInvalidMemberError
            The member wasn't involved in the transaction
        """
        log.info(f"Marking transaction {transaction.id} as delivered by {reactor.id}")

        if transaction.cancelled:
            log.info(f"Transaction {transaction.id} alrady cancelled")
            raise TransactionCancelledError(transaction=transaction)

        if reactor.id == transaction.buyer_id:
            is_buyer = True
            log.info("Processing buyer marked delivered")
        elif reactor.id == transaction.seller_id:
            is_buyer = False
            log.info("Processing seller marked delivered")
        else:
            log.info(
                f"Ignoring marking delivered of {transaction.id} from invalid member"
            )
            raise TransactionInvalidMemberError(transaction=transaction, member=reactor)

        if is_buyer and transaction.buyer_delivered:
            log.info("Ignoring. Buyer already marked as delivered")
            return transaction
        elif is_buyer is False and transaction.seller_delivered:
            log.info("Ignoring. Seller already marked as delivered")
            return transaction

        # Start with empty list so we can add fields as we go
        fields = []

        if is_buyer:
            fields.append("buyer_delivered")
            transaction.buyer_delivered = True
        else:
            fields.append("seller_delivered")
            transaction.seller_delivered = True

        if transaction.buyer_delivered and transaction.seller_delivered:
            transaction.delivered_date = datetime.now(timezone.utc)
            fields.append("delivered_date")

        log.debug(f"Transaction: {transaction}")

        return await self.save_transaction(
            transaction=transaction, fields=fields, session=session
        )

    async def mark_transaction_paid(
        self,
        transaction: Transaction,
        reactor: DiscordMember,
        session: AsyncSession | None = None,
    ) -> Transaction:
        """Mark the transaction as paid.

        Parameters
        ----------
        transaction : Transaction
            The transaction to be updated
        reactor : DiscordMember
            The member who made the reaction
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Transaction
            The updated transaction

        Raises
        ------
        TransactionCancelledError
            The transaction was already cancelled
        TransactionInvalidMemberError
            The member wasn't involved in the transaction
        """
        log.info(f"Marking transaction {transaction.id} as paid by {reactor.id}")

        if transaction.cancelled:
            log.info(f"Transaction {transaction.id} alrady cancelled")
            raise TransactionCancelledError(transaction=transaction)

        if reactor.id == transaction.buyer_id:
            is_buyer = True
            log.info("Processing buyer marked paid")
        elif reactor.id == transaction.seller_id:
            is_buyer = False
            log.info("Processing seller marked paid")
        else:
            log.info(
                f"Ignoring marking payment of {transaction.id} from invalid member"
            )
            raise TransactionInvalidMemberError(transaction=transaction, member=reactor)

        if is_buyer and transaction.buyer_paid:
            log.info("Ignoring. Buyer already marked as paid")
            return transaction
        elif is_buyer is False and transaction.seller_paid:
            log.info("Ignoring. Seller already marked as paid")
            return transaction

        # Start with empty list so we can add fields as we go
        fields = []

        if is_buyer:
            fields.append("buyer_paid")
            transaction.buyer_paid = True
        else:
            fields.append("seller_paid")
            transaction.seller_paid = True

        if transaction.buyer_paid and transaction.seller_paid:
            transaction.paid_date = datetime.now(timezone.utc)
            fields.append("paid_date")

        log.debug(f"Transaction: {transaction}")

        return await self.save_transaction(
            transaction=transaction, fields=fields, session=session
        )

    async def get_transaction_by_bot_message_id(
        self,
        bot_message_id: int,
        bot_message_service: BotMessageService,
        session: AsyncSession | None = None,
    ) -> Transaction | None:
        """
        Find the Transaction associated with a given BotMessage ID.

        Parameters
        ----------
        bot_message_id : int
            The discord message_id of the bot message
        bot_message_service: BotMessageService
            An instance of the BotMessageService to do the lookup
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[Transaction]
            The associated transaction, or None if not found
        """
        # Get the BotMessage
        async with self._get_session(session) as session:
            bot_message = await bot_message_service.get_bot_message_by_message_id(
                bot_message_id, session=session
            )
            if not bot_message:
                return None

            # Get the Transaction linked to this BotMessage
            transaction = await self.get_transaction(
                bot_message.transaction_id, session=session
            )
            return transaction
