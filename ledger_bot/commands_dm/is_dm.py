"""Check if the message is a direct message."""

import logging

import discord
from discord import Message

log = logging.getLogger(__name__)


def is_dm(message: Message) -> bool:
    """
    Check if the message is a direct message.

    Paramaters
    ----------
    message : Message
    The message to check

    Returns
    -------
    True if it's a DM, false otherwise.
    """
    return isinstance(message.channel, discord.DMChannel)
