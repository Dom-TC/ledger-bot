"""SQLite implementation of BotMessageStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import BotMessage

from .abstracts import BotMessageStorageABC

log = logging.getLogger(__name__)


class BotMessageStorage(BotMessageStorageABC):
    """SQLite implementation of BotMessageStorageABC."""

    async def get_bot_message(
        self, record_id: int, session: AsyncSession
    ) -> Optional[BotMessage]:
        log.info(f"Getting bot_message with record_id {record_id}")
        result: BotMessage | None = await session.get(BotMessage, record_id)
        return result

    async def add_bot_message(
        self, bot_message: BotMessage, session: AsyncSession
    ) -> BotMessage:
        log.info(f"Adding bot_message for {bot_message.transaction_id}")
        session.add(bot_message)
        await session.flush()
        await session.refresh(bot_message)
        log.info(f"Bot_message added with id {bot_message.id}")
        return bot_message

    async def list_bot_message(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[BotMessage]]:
        log.info(f"Listing bot_messages that match query {filters}")
        query = select(BotMessage)
        if filters:
            query = query.where(*filters)
        result = await session.execute(query)
        bot_messages = list(result.scalars().all())
        log.info(f"Found {len(bot_messages)} transactions")
        return bot_messages if bot_messages else None

    async def delete_bot_message(
        self, bot_message: BotMessage, session: AsyncSession
    ) -> None:
        log.info(
            f"Deleting bot_message id {bot_message.id} (transaction {bot_message.transaction_id})"
        )
        await session.delete(bot_message)
        await session.flush()
