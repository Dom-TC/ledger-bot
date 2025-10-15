"""DM command - version."""

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_version(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - version."""
    response = f"Version: {client.version}"

    if bot_id := client.config.bot_id:
        response = f"{response} ({bot_id})"

    await dm_channel.send(response)
