"""A service to provide interfacing for BotMessageStorage."""

import logging
from datetime import datetime, timezone
from typing import Optional

from asyncache import cached
from discord import Message
from discord.interactions import InteractionMessage
from sqlalchemy import and_, or_

from ledger_bot.errors import BotMessageInvalidTransactionError
from ledger_bot.models import BotMessage, Transaction
from ledger_bot.storage import BotMessageStorage

log = logging.getLogger(__name__)


class BotMessageService:
    def __init__(self, bot_message_storage: BotMessageStorage, bot_id: str):
        self.bot_message_storage = bot_message_storage
        self.bot_id = bot_id

    async def get_bot_message(self, record_id: int) -> Optional[BotMessage]:
        """Get a bot_message with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved

        Returns
        -------
        Optional[BotMessage]
            The bot_message object
        """
        bot_message = await self.bot_message_storage.get_bot_message(
            record_id=record_id
        )
        return bot_message

    async def save_bot_message(
        self,
        message: Message | InteractionMessage,
        transaction: Transaction,
    ) -> BotMessage:
        """Save the message into a bot_message for a given transaction.

        Parameters
        ----------
        message : Message | InteractionMessage
            The message
        transaction : Transaction
            The transaction

        Returns
        -------
        BotMessage
            The saved bot_message

        Raises
        ------
        BotMessageInvalidTransactionError
            Transaction doesn't have a record id
        """
        log.info(f"Saving bot message({message.id}) for transaction {transaction.id}")

        if transaction.id is None:
            log.info(
                "Transaction doesn't have a record id. Can't store message. Skipping..."
            )
            raise BotMessageInvalidTransactionError(transaction=transaction)

        bot_message = BotMessage(
            message_id=message.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id if message.guild else "",
            transaction_id=transaction.id,
            creation_date=datetime.now(timezone.utc),
            bot_id=self.bot_id,
        )

        log.debug(f"Storing bot_message: {bot_message}")
        return await self.bot_message_storage.add_bot_message(bot_message=bot_message)

    async def get_bot_message_by_message_id(
        self, message_id: int
    ) -> Optional[BotMessage]:
        """Get the BotMessage that for a given message id.

        Parameters
        ----------
        message_id : int
            The message id of the bot message being searched for

        Returns
        -------
        Optional[BotMessage]
            The BotMessage
        """
        filter_ = BotMessage.message_id == message_id
        bot_messages = await self.bot_message_storage.list_bot_message(filter_)

        return bot_messages[0] if bot_messages else None

    async def delete_bot_message(self, bot_message: BotMessage) -> None:
        """Delete the specified bot_message.

        Parameters
        ----------
        bot_message : BotMessage
            The bot_message to be deleted
        """
        log.info(f"Deleting bot_message {bot_message.id}")
        await self.bot_message_storage.delete_bot_message(bot_message)
