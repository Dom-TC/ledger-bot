"""Helper function to get the DM channel for sending messages."""

import logging
from typing import Union

import discord

log = logging.getLogger(__name__)


async def get_dm_channel(
    user: Union[discord.Member, discord.User]
) -> discord.DMChannel:
    """Helper function to get the DM channel for sending messages."""
    return user.dm_channel if user.dm_channel else await user.create_dm()
