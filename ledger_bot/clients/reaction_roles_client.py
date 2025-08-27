"""A mixin for dealing with reaction roles."""

import logging
from typing import TYPE_CHECKING, Any, Dict

import arrow
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.services import Service

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class ReactionRolesClient(ExtendedClient):
    def __init__(
        self,
        config: Dict[str, Any],
        scheduler: AsyncIOScheduler,
        service: Service,
        session_factory: async_sessionmaker[AsyncSession],
        **kwargs,
    ) -> None:
        self.service = service
        self.session_factory = session_factory

        initial_refresh_time = arrow.utcnow().shift(minutes=1).datetime
        scheduler.add_job(
            self.refresh_reaction_role_caches,
            name="Refresh reaction-role watched messages",
            trigger="cron",
            hour=config["reaction_role_refresh_time"]["hour"],
            minute=config["reaction_role_refresh_time"]["minute"],
            second=config["reaction_role_refresh_time"]["second"],
            coalesce=True,
            next_run_time=initial_refresh_time,
            misfire_grace_time=10,
        )
        super().__init__(**kwargs)

    async def refresh_reaction_role_caches(self) -> None:
        log.info("Refreshing reaction-role watched messages")
        watched_message_ids = (
            await self.service.reaction_role.list_watched_message_ids()
        )
        log.info(f"Watching {watched_message_ids}")

    async def handle_role_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        watched_message_ids = (
            self.service.reaction_role.watched_message_ids
            if len(self.service.reaction_role.watched_message_ids) > 0
            else await self.service.reaction_role.list_watched_message_ids()
        )

        if str(payload.message_id) not in watched_message_ids:
            return False

        if self.user is await self.get_or_fetch_user(payload.user_id):
            log.info("Ignoring role-reaction from self")
            return False

        log.info(
            f"Handling reaction role request - {payload.emoji} on {payload.message_id} from {payload.member}"
        )

        if not payload.guild_id or not payload.message_id or payload.emoji:
            log.info(f"Invalid payload {payload}")
            return False

        reaction_role = await self.service.reaction_role.get_reaction_role_by_reaction(
            server_id=payload.guild_id,
            message_id=int(payload.message_id),
            reaction=str(payload.emoji),
        )
        log.debug(f"Reaction role: {reaction_role}")

        if reaction_role is None:
            log.info("No reaction-role mapping found")
            return False

        # We've already done these checks for this function to be called, but we do it again now to handle MyPy's errors.
        guild_id = payload.guild_id
        if guild_id is None:
            return False
        guild = self.get_guild(guild_id)
        if guild is None:
            return False
        if payload.member is None:
            return False

        role = guild.get_role(int(reaction_role.role_id))

        if role is None:
            log.warning(f"No role found with ID {reaction_role.role_id}")
            return False

        try:
            if role not in payload.member.roles:
                await payload.member.add_roles(
                    role, reason="Reaction role", atomic=False
                )
        except discord.Forbidden as err:
            log.error(
                f"You don't have permission to add the role {role} to {payload.member}: {err}"
            )
        except discord.HTTPException as err:
            log.error(
                f"An HTTP exception occured while adding the role {role} to {payload.member}: {err}"
            )

        return True

    async def handled_role_reaction_removal(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        watched_message_ids = (
            self.service.reaction_role.watched_message_ids
            if len(self.service.reaction_role.watched_message_ids) > 0
            else await self.service.reaction_role.list_watched_message_ids()
        )

        if str(payload.message_id) not in watched_message_ids:
            return False

        if self.user is await self.get_or_fetch_user(payload.user_id):
            log.info("Ignoring role-reaction-removal from self")
            return False

        log.info(
            f"Handling reaction role removal request - {payload.emoji} on {payload.message_id} from {payload.user_id}"
        )

        # We've already done these checks for this function to be called, but we do it again now to handle MyPy's errors.
        guild_id = payload.guild_id
        if guild_id is None:
            return False
        guild = self.get_guild(guild_id)
        if guild is None:
            return False
        if payload.user_id is None:
            return False

        reaction_role = await self.service.reaction_role.get_reaction_role_by_reaction(
            server_id=guild_id,
            message_id=payload.message_id,
            reaction=str(payload.emoji),
        )
        log.debug(f"Reaction role: {reaction_role}")

        if reaction_role is None:
            log.info("No reaction-role mapping found")
            return False

        role = guild.get_role(int(reaction_role.role_id))
        member = guild.get_member(payload.user_id)

        if role is None:
            log.warning(f"No role found with ID {reaction_role.role_id}")
            return False

        if member is None:
            log.warning(f"No role found with ID {payload.user_id}")
            return False

        try:
            if role in member.roles:
                await member.remove_roles(role, reason="Reaction role", atomic=False)
        except discord.Forbidden as err:
            log.error(
                f"You don't have permission to remove the role {role} to {payload.member}: {err}"
            )
        except discord.HTTPException as err:
            log.error(
                f"An HTTP exception occured while removing the role {role} to {payload.member}: {err}"
            )

        return True
