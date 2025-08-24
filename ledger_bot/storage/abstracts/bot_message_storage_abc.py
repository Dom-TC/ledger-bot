"""The abstraction interface for bot_message_storage."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.sql import ColumnElement

from ledger_bot.models import BotMessage


class BotMessageStorageABC(ABC):
    @abstractmethod
    async def get_bot_message(self, record_id: int) -> Optional[BotMessage]:
        """Get a bot_message by a record id.

        Parameters
        ----------
        record_id : int
            The id of the bot_message

        Returns
        -------
        Optional[BotMessage]
            The bot_message object, if found.
        """
        ...

    @abstractmethod
    async def add_bot_message(self, bot_message: BotMessage) -> BotMessage:
        """Add a bot_message to the database.

        Parameters
        ----------
        bot_message : BotMessage
            The bot_message object to add to the database.

        Returns
        -------
        BotMessage
            The bot_message object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_bot_message(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[BotMessage]]:
        """List bot_messages that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that bot_messages must match.

        Returns
        -------
        Optional[List[BotMessage]]
            A list of bot_messages that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_bot_message(self, bot_message: BotMessage) -> None:
        """Deletes the bot_message with the given id.

        Parameters
        ----------
        bot_message : BotMessage
            The bot_message to be deleted
        """
        ...
