"""Mixin for dealing with the Transactions table."""

import logging
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from aiohttp import ClientSession

from ledger_bot.models import BotMessageAirtable, TransactionAirtable

from .base_storage import BaseStorage

log = logging.getLogger(__name__)


class TransactionsMixin(BaseStorage):
    wines_url: str
    bot_id: str
    find_bot_message_by_message_id: Callable  # This is definited in the BotMessagesMixin

    async def update_transaction(
        self,
        record_id: str,
        transaction_record: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> TransactionAirtable:
        """
        Updates a specific transaction record.

        Paramaters
        ----------
        record_id : str
            The primary key of the transaction to update

        transaction_record : dict
            The records to update

        session : ClientSession, optional
            The ClientSession to use

        """
        record = await self._update(
            self.wines_url + "/" + record_id, transaction_record, session
        )

        return TransactionAirtable.from_airtable(record)

    async def save_transaction(
        self, transaction: TransactionAirtable, fields: List[str] | None = None
    ) -> TransactionAirtable:
        """
        Saves the provided Transaction.

        If it has no primary key, inserts a new instance, otherwise updates the old instance.
        If a list of fields are specified, only saves/updates those fields.

        Paramaters
        ----------
        transaction : Transaction
            The transaction to insert

        fields : Optional
            The fields to save / update

        """
        fields = fields or [
            "seller_id",
            "buyer_id",
            "wine",
            "price",
            "sale_approved",
            "delivered",
            "paid",
            "cancelled",
            "creation_date",
            "approved_date",
            "paid_date",
            "delivered_date",
            "cancelled_date",
            "guild_id",
            "channel_id",
            "bot_message_id",
        ]

        # Always store bot_id
        transaction.bot_id = self.bot_id or ""
        if "bot_id" not in fields:
            fields.append("bot_id")

        transaction_data = transaction.to_airtable(fields=fields)
        log.info(f"Adding transaction data: {transaction_data['fields']}")
        if transaction.record_id:
            log.info(f"Updating transaction with id: {transaction_data['id']}")
            return await self.update_transaction(
                transaction_data["id"], transaction_data["fields"]
            )
        else:
            log.info("Adding transaction to Airtable")
            return await self.insert_transaction(transaction_data["fields"])

    async def _list_transactions(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ) -> list[TransactionAirtable]:
        records = await self._list(self.wines_url, filter_by_formula, session)

        transactions = []
        for record in records:
            transaction = TransactionAirtable.from_airtable(record)
            transactions.append(transaction)

        return transactions

    async def _list_all_transactions(
        self,
        filter_by_formula: Optional[str] = None,
        sort: Optional[list[str]] = None,
        session: Optional[ClientSession] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        return self._iterate(
            self.wines_url,
            filter_by_formula=filter_by_formula,
            sort=sort,
            session=session,
        )

    async def _retrieve_transaction(
        self, transaction_id: str, session: Optional[ClientSession] = None
    ) -> TransactionAirtable:
        log.debug(f"Retrieving transaction with id {transaction_id}")
        record = await self._get(f"{self.wines_url}/{transaction_id}", session=session)
        return TransactionAirtable.from_airtable(record)

    async def insert_transaction(
        self, record: Dict[str, Any], session: Optional[ClientSession] = None
    ) -> TransactionAirtable:
        """
        Inserts a transaction into the table.

        Paramaters
        ----------
        record : dict
            The record to insert

        session : ClientSession, optional
            The ClientSession to use

        Returns
        -------
        dict
            A Dictionary containing the inserted record
        """
        record = await self._insert(self.wines_url, record, session)
        return TransactionAirtable.from_airtable(record)

    async def find_transaction_by_bot_message_id(
        self, message_id: str
    ) -> TransactionAirtable | None:
        """Takes a message and returns any associated Transactions, else returns None."""
        log.info(f"Searching for transactions relating to bot message {message_id}")
        bot_message = await self.find_bot_message_by_message_id(message_id)
        if bot_message is None:
            log.info("No matching records found")
            return None
        else:
            transaction = await self._retrieve_transaction(bot_message.transaction_id)
            return transaction or None

    async def delete_transaction(
        self, record_id: str, session: ClientSession | None = None
    ) -> None:
        """Delete the specified bot_message record."""
        records_to_delete = [record_id]
        log.info(f"Deleting records {records_to_delete}")
        await self._delete(self.wines_url, records_to_delete, session)

    async def get_completed_transactions(
        self, hours_completed: int = 0
    ) -> List[TransactionAirtable] | None:
        """
        Get a list of transactions that are completed.

        A transaction is considered completed when sale_approved, buyer_marked_delivered, seller_marked_delivered, buyer_marked_paid, and seller_marked_paid are all true.

        Parameters
        ----------
        hours_completed : int, optional
            The minumum number of hours ago a transaction must have been completed for it to be included, by default 0

        Returns
        -------
        Optional[List[Transaction]]
            A list of Transactions, or None.
        """
        filter_formula = f"AND({{sale_approved}},{{buyer_marked_delivered}},{{buyer_marked_paid}},{{seller_marked_delivered}},{{seller_marked_paid}},IF(DATETIME_DIFF(TODAY(),{{delivered_date}},'hours')>{hours_completed},TRUE(),FALSE()),IF(DATETIME_DIFF(TODAY(),{{paid_date}},'hours')>{hours_completed},TRUE(),FALSE()))"

        transactions = await self._list_transactions(filter_formula)
        if len(transactions) == 0:
            return None
        else:
            return transactions

    async def get_users_transaction(
        self, user_id: str
    ) -> List[TransactionAirtable] | None:
        filter_formula = f"OR(IF({{seller_discord_id}}={user_id},TRUE(),FALSE()),IF({{buyer_discord_id}}={user_id},TRUE(),FALSE()))"

        transactions = await self._list_transactions(filter_formula)

        if len(transactions) == 0:
            return None
        else:
            return transactions

    async def get_transaction_from_record_id(
        self, record_id: str
    ) -> TransactionAirtable:
        """Returns the transaction object for the transaction with a given AirTable record id."""
        log.info(f"Finding transaction with record {record_id}")
        transaction = await self._retrieve_transaction(record_id)
        return transaction

    async def get_all_transactions(self) -> Optional[List[TransactionAirtable]]:
        log.info("Getting all transactions")

        transactions = []
        async for record in await self._list_all_transactions():
            transaction = TransactionAirtable.from_airtable(record)
            transactions.append(transaction)

        return transactions if transactions else None

    async def get_transaction_by_row_id(
        self, row_id: int
    ) -> TransactionAirtable | None:
        """Returns the transaction with the corrosponding row id."""
        log.info(f"Getting transactions with row_id {row_id}")

        filter_formula = f"IF(row_id={row_id},TRUE(), FALSE())"

        transactions = await self._list_transactions(filter_formula)
        if len(transactions) == 0:
            return None
        else:
            return transactions[0]
