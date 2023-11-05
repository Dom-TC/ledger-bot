"""DM command - version."""

import logging
import os
import subprocess
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_version(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
):
    """DM command - version."""
    git_version = os.getenv("BOT_VERSION", client.config["emojis"]["unknown_version"])
    try:
        # If tagged version, use that instead.
        git_version = (
            subprocess.check_output(["git", "describe", "--tags"])
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError as error:
        log.warning(f"Git command failed with code: {error.returncode}")
    except FileNotFoundError:
        log.warning("Git command not found")
    response = f"Version: {git_version}"
    if bot_id := client.config["id"]:
        response = f"{response} ({bot_id})"
    await dm_channel.send(response)
