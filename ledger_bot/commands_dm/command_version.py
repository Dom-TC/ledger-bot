"""DM command - version."""

import logging
import os
from shutil import which
from subprocess import CalledProcessError, check_output
from typing import TYPE_CHECKING

import discord
from sqlalchemy import text

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_version(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - version."""
    response = f"Version: {client.version}"

    if bot_id := client.config["id"]:
        response = f"{response} ({bot_id})"

    await dm_channel.send(response)
