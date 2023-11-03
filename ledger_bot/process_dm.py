"""Process messages sent via DM."""

import logging
import os
import subprocess
from typing import TYPE_CHECKING, Union

import discord
from discord import Message

from .reactions import add_reaction

if TYPE_CHECKING:
    from LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def get_dm_channel(
    user: Union[discord.Member, discord.User]
) -> discord.DMChannel:
    """Helper function to get the DM channel for sending messages."""
    return user.dm_channel if user.dm_channel else await user.create_dm()


def is_dm(message: Message) -> bool:
    """
    Check if the message is a Direct message.

    Paramaters
    ----------
    message : Message
    The message to check

    Returns
    -------
    True if it's a DM, false otherwise.
    """
    return isinstance(message.channel, discord.DMChannel)


async def process_dm(client: "LedgerBot", message: Message):
    """
    Processes the provided message.

    Paramaters
    ----------
    client : LedgerBot
        The client being called

    message : Message
        The message being processed
    """
    # Ignore any messages sent by ledger-bot
    if message.author == client.user:
        log.debug("Ignoring own message")
        return

    log.info(
        f"Received direct message (ID: {message.id}) from {message.author}: {message.content}"
    )

    # We don't care about capitalisation, so set everything to lower
    message_content = message.content.lower().strip()

    # Get the DM channel so we can later respond to the message
    dm_channel = await get_dm_channel(message.author)

    if message_content == "!version":
        git_version = os.getenv(
            "BOT_VERSION", client.config["emojis"]["unknown_version"]
        )
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
        return
    elif (
        message_content.startswith("!dev")
        and message.author.id in client.config["maintainer_ids"]
    ):
        request = message_content.removeprefix("!dev ")
        log.info(f"Processing dev mode request ({request}) from {message.author.name}")

        if request.startswith("add_reaction"):
            message_id = request.split(" ")[1]
            reaction = request.split(" ")[2]

            await add_reaction(client, message_id, reaction)
