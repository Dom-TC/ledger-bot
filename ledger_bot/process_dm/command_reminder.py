"""DM command - reminder."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_help_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_reminder(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
):
    """DM command - watch."""
