"""An extension to discord.pys base client."""

import logging
import os
from shutil import which
from subprocess import CalledProcessError, check_output
from typing import Any, Optional, Union

import discord
from discord import app_commands
from discord.abc import GuildChannel, PrivateChannel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.config import Config

log = logging.getLogger(__name__)


class ExtendedClient(discord.Client):
    # In reality, this will only ever be a discord.Guild object once the bot is running
    # but we temporarily set it to discord.Object during setup.
    guild: discord.Guild | discord.Object | None

    session_factory: async_sessionmaker[AsyncSession]

    config: Config

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

    async def get_or_fetch_guild(self, guild_id: int) -> discord.Guild:
        if guild := self.get_guild(guild_id):
            return guild
        else:
            return await self.fetch_guild(guild_id)

    async def get_or_fetch_member(
        self, user: int | discord.User, guild: int | discord.Guild
    ) -> discord.Member:
        user_id = user.id if isinstance(user, discord.User) else user
        guild_obj = (
            await self.get_or_fetch_guild(guild) if isinstance(guild, int) else guild
        )

        if member := guild_obj.get_member(user_id):
            return member
        else:
            return await guild_obj.fetch_member(user_id)

    async def is_admin_or_maintainer(self, user_id: int) -> bool:
        if isinstance(self.guild, discord.Guild):
            member = self.guild.get_member(user_id)

            if member is not None:
                return (member.get_role(self.config.admin_role) is not None) or (
                    member.id in self.config.maintainer_ids
                )
            else:
                return False
        else:
            log.info(
                "Guild hasn't been instantised, so can't check if user is an admin"
            )
            return False

    async def get_version_number(self):
        git_version = os.getenv("BOT_VERSION", self.config.emojis.unknown_version)

        git_path = which("git")
        if git_path is None:
            response = self.config.emojis.unknown_version
            log.error("Can't find git path.")
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

        async with self.session_factory() as session:
            alembic_db = await session.execute(
                text("SELECT version_num FROM alembic_version")
            )
            alembic_version = alembic_db.scalar_one_or_none()

        response = f"{git_version}-db{alembic_version}"
        return response
