"""Mixin for dealing with the BotMessages table."""

import datetime
import logging
from typing import Dict, List, Optional

import discord
from aiohttp import ClientSession

from ledger_bot.models import BotMessage, Transaction

from .base_storage import BaseStorage

log = logging.getLogger(__name__)


class BotMessagesMixin(BaseStorage):
    bot_messages_url: str
    bot_id: str

    async def _insert_bot_message(
        self,
        record: Dict[str, str | List[str]],
        session: Optional[ClientSession] = None,
    ) -> Dict[str, str | List[str]]:
        return await self._insert(self.bot_messages_url, record, session)

    async def record_bot_message(
        self,
        message: discord.Message | discord.interactions.InteractionMessage,
        transaction: Transaction,
    ) -> Dict[str, str | List[str]] | None:
        """Create a record in bot_messages for a given bot_message.

        Paramaters
        ----------
        message : Union[discord.Message, discord.interactions.InteractionMessage]
            The message to store
        transaction : Transaction
            The transaction the message is referencing

        Returns
        -------
        dict
            A dictionary containing the inserted record
        """
        if transaction.record_id is None:
            log.info(
                "Transaction doesn't have a record id. Can't store message. Skipping..."
            )
            return None

        data: Dict[str, str | List[str]] = {
            "bot_message_id": str(message.id),
            "channel_id": str(message.channel.id),
            "guild_id": str(message.guild.id) if message.guild else "",
            "transaction_id": [transaction.record_id],
            "message_creation_date": str(datetime.datetime.utcnow().isoformat()),
            "bot_id": self.bot_id or "",
        }
        log.info(f"Storing bot_message: {data}")
        return await self._insert_bot_message(record=data)

    async def _list_bot_messages(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ) -> List[Dict[str, str | List[str]]]:
        return await self._list(self.bot_messages_url, filter_by_formula, session)

    async def find_bot_message_by_message_id(
        self, bot_message_id: str, session: Optional[ClientSession] = None
    ) -> BotMessage | None:
        log.debug(f"Finding bot_message with id {bot_message_id}")
        bot_messages = await self._list_bot_messages(
            filter_by_formula="{{bot_message_id}}={value}".format(value=bot_message_id),
            session=session,
        )

        if bot_messages is None:
            return None
        else:
            record = bot_messages[0]
        return BotMessage.from_airtable(record)

    async def delete_bot_message(
        self, record_id: str, session: ClientSession | None = None
    ) -> None:
        """Delete the specified bot_message record."""
        records_to_delete = [record_id]
        log.info(f"Deleting records {records_to_delete}")
        await self._delete(self.bot_messages_url, records_to_delete, session)

    async def find_bot_message_by_record_id(
        self, record_id: str, session: Optional[ClientSession] = None
    ) -> BotMessage:
        log.debug(f"Finding bot_message with record {record_id}")
        record = await self._get(
            f"{self.bot_messages_url}/{record_id}", session=session
        )
        return BotMessage.from_airtable(record)
