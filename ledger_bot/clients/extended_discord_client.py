"""An extension to discord.pys base client."""

import logging
from typing import Any, Dict, Optional, Union

import discord
from discord import app_commands
from discord.abc import GuildChannel, PrivateChannel

log = logging.getLogger(__name__)


class ExtendedDiscordClient(discord.Client):
    # In reality, this will only ever be a discord.Guild object once the bot is running,
    # but we temporarily set it to discord.Object during setup.
    guild: discord.Guild | discord.Object | None

    config: Dict[str, Any]

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.tree = app_commands.CommandTree(self)

    async def get_or_fetch_channel(
        self, channel_id: int
    ) -> Optional[Union[GuildChannel, PrivateChannel, discord.Thread]]:
        if channel := self.get_channel(channel_id):
            return channel
        else:
            return await self.fetch_channel(channel_id)

    async def get_or_fetch_user(self, user_id: int) -> discord.User:
        if user := self.get_user(user_id):
            return user
        else:
            return await self.fetch_user(user_id)

    async def is_admin_or_maintainer(self, user_id: int) -> bool:
        if isinstance(self.guild, discord.Guild):
            member = self.guild.get_member(user_id)

            if member is not None:
                return (member.get_role(self.config["admin_role"]) is not None) or (
                    member.id in self.config["maintainer_ids"]
                )
            else:
                return False
        else:
            log.info(
                "Guild hasn't been instantised, so can't check if user is an admin"
            )
            return False
