"""DM command - version."""

import logging
import os
from shutil import which
from subprocess import CalledProcessError, check_output
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

    git_path = which("git")
    if git_path is None:
        response = "Can't find git command"
    else:
        try:
            # If tagged version, use that instead.
            git_version = (
                check_output([git_path, "describe", "--tags"])  # nosec
                .decode("utf-8")
                .strip()
            )
        except CalledProcessError as error:
            log.warning(f"Git command failed with code: {error.returncode}")
        except FileNotFoundError:
            log.warning("Git command not found")
        response = f"Version: {git_version}"
        if bot_id := client.config["id"]:
            response = f"{response} ({bot_id})"

    await dm_channel.send(response)
