"""SQLite implementation of BotMessageStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import BotMessage

from .abstracts import BotMessageStorageABC

log = logging.getLogger(__name__)


class BotMessageStorage(BotMessageStorageABC):
    """SQLite implementation of BotMessageStorageABC."""

    def __init__(self, session_factory: sessionmaker):
        """Initialise BotMessageStorage.

        Parameters
        ----------
        session_factory : Callable[[], AsyncSession]
            Factory to produce new SQLAlchemy AsyncSession objects.
        """
        self._session_factory = session_factory

    async def get_bot_message(self, record_id: int) -> Optional[BotMessage]:
        async with self._session_factory() as session:
            log.info(f"Getting bot_message with record_id {record_id}")
            result = await session.get(BotMessage, record_id)
            return result

    async def add_bot_message(self, bot_message: BotMessage) -> BotMessage:
        async with self._session_factory() as session:
            log.info(f"Adding bot_message for {bot_message.transaction.id}")
            session.add(bot_message)
            await session.commit()
            await session.refresh(bot_message)
            log.info(f"Bot_message added with id {bot_message.id}")
            return bot_message

    async def list_bot_message(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[BotMessage]]:
        async with self._session_factory() as session:
            log.info(f"Listing bot_messages that match query {filters}")
            query = select(BotMessage)
            if filters:
                query = query.where(*filters)
            result = await session.execute(query)
            bot_messages = result.scalars().all()
            log.info(f"Found {len(bot_messages)} transactions")
            return bot_messages if bot_messages else None

    async def delete_bot_message(self, bot_message: BotMessage) -> None:
        async with self._session_factory() as session:
            log.info(
                f"Deleting bot_message id {bot_message.id} (transaction {bot_message.transaction.id})"
            )
            await session.delete(bot_message)
            await session.commit()
