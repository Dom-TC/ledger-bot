"""A service to provide interfacing for BotMessageStorage."""

import logging
from datetime import datetime, timezone
from typing import List

from discord import Message
from discord.interactions import InteractionMessage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.core import Config
from ledger_bot.errors import BotMessageInvalidTransactionError
from ledger_bot.models import BotMessage, Transaction
from ledger_bot.storage import BotMessageStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class BotMessageService(ServiceHelpers):
    def __init__(
        self,
        bot_message_storage: BotMessageStorage,
        config: Config,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.bot_message_storage = bot_message_storage
        self.config = config

        super().__init__(session_factory)

    async def get_bot_message(
        self, record_id: int, session: AsyncSession | None = None
    ) -> BotMessage | None:
        """Get a bot_message with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[BotMessage]
            The bot_message object
        """
        async with self._get_session(session) as session:
            bot_message = await self.bot_message_storage.get_bot_message(
                record_id=record_id,
                session=session,
            )
            return bot_message

    async def save_bot_message(
        self,
        message: Message | InteractionMessage,
        transaction: Transaction,
        session: AsyncSession | None = None,
    ) -> BotMessage:
        """Save the message into a bot_message for a given transaction.

        Parameters
        ----------
        message : Message | InteractionMessage
            The message
        transaction : Transaction
            The transaction
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        BotMessage
            The saved bot_message

        Raises
        ------
        BotMessageInvalidTransactionError
            Transaction doesn't have a record id
        """
        if transaction.id is None:
            log.info(
                "Transaction doesn't have a record id. Can't store message. Skipping..."
            )
            raise BotMessageInvalidTransactionError(transaction=transaction)

        log.info(f"Saving bot message({message.id}) for transaction {transaction.id}")

        bot_message = BotMessage(
            message_id=message.id,
            channel_id=message.channel.id,
            guild_id=message.guild.id if message.guild else "",
            transaction_id=transaction.id,
            creation_date=datetime.now(timezone.utc),
            bot_id=self.config.bot_id,
        )

        log.debug(f"Storing bot_message: {bot_message}")
        async with self._get_session(session) as session:
            bot_message = await self.bot_message_storage.add_bot_message(
                bot_message=bot_message, session=session
            )
            await session.commit()
            return bot_message

    async def get_bot_message_by_message_id(
        self, message_id: int, session: AsyncSession | None = None
    ) -> BotMessage | None:
        """Get the BotMessage that for a given message id.

        Parameters
        ----------
        message_id : int
            The message id of the bot message being searched for
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[BotMessage]
            The BotMessage
        """
        async with self._get_session(session) as session:
            filter_ = BotMessage.message_id == message_id
            bot_messages = await self.bot_message_storage.list_bot_message(
                filter_, session=session
            )

            return bot_messages[0] if bot_messages else None

    async def delete_bot_message(
        self, bot_message: BotMessage, session: AsyncSession | None = None
    ) -> None:
        """Delete the specified bot_message.

        Parameters
        ----------
        bot_message : BotMessage
            The bot_message to be deleted
        session : AsyncSession | None, optional
            An optional session, by default None
        """
        log.info(f"Deleting bot_message {bot_message.id}")
        async with self._get_session(session) as session:
            await self.bot_message_storage.delete_bot_message(
                bot_message, session=session
            )
            await session.commit()

    async def get_bot_messages_by_transaction_id(
        self, transaction_id: int, session: AsyncSession | None = None
    ) -> List[BotMessage] | None:
        """Get all the bot messages for a given transaction id."""
        log.debug(f"Getting bot messages for transaction {transaction_id}")

        async with self._get_session(session) as session:
            messages = await self.bot_message_storage.list_bot_message(
                BotMessage.transaction_id == transaction_id,
                session=session,
            )
            return messages
