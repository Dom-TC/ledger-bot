"""Processes the provided message."""

import logging
from typing import TYPE_CHECKING

from discord import Message

from .command_dev import command_dev
from .command_help import command_help
from .command_list import command_list
from .command_version import command_version
from .get_dm_channel import get_dm_channel

if TYPE_CHECKING:
    from LedgerBot import LedgerBot

log = logging.getLogger(__name__)


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
        log.info("Recognised command: !version")
        await command_version(client=client, message=message, dm_channel=dm_channel)
        return
    elif message_content == "!list":
        log.info("Recognised command: !list")
        await command_list(client=client, message=message, dm_channel=dm_channel)
    elif (
        message_content.startswith("!dev")
        and message.author.id in client.config["maintainer_ids"]
    ):
        log.info("Recognised command: !dev")
        await command_dev(client=client, message=message, dm_channel=dm_channel)
        return
    elif message_content == "!help":
        log.info("Recognised command: !help")
        await command_help(client=client, message=message, dm_channel=dm_channel)
    else:
        await dm_channel.send(
            "I'm afraid I don't recognise that command.  Please use `!help` for a list of what I can do."
        )
