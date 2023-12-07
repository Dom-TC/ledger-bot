"""Process messages."""

import logging
from typing import TYPE_CHECKING

from discord import Message

if TYPE_CHECKING:
    from .LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def process_message(client: "LedgerBot", message: Message) -> None:
    """Processes the provided message."""
    pass
