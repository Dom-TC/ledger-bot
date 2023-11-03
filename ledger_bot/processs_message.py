"""Process messages."""

import logging
from typing import TYPE_CHECKING

from discord import Message

if TYPE_CHECKING:
    from LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def process_message(client: "LedgerBot", message: Message):
    """Processes the provided message."""
    if message.content == "add_member":
        log.debug(f"Adding member: {message.author}")
        await client.storage.get_or_add_member(message.author)
