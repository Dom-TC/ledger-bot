"""A mixin for dealing with reaction roles."""

import logging
from typing import Any, Dict

import arrow
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ledger_bot.storage import ReactionRolesStorage

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class ReactionRolesClient(ExtendedClient):
    def __init__(
        self,
        config: Dict[str, Any],
        scheduler: AsyncIOScheduler,
        reaction_roles_storage: ReactionRolesStorage,
        **kwargs,
    ) -> None:
        self.reaction_roles_storage = reaction_roles_storage

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
            await self.reaction_roles_storage.list_watched_message_ids()
        )
        log.info(f"Watching {watched_message_ids}")

    async def handle_role_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        watched_message_ids = (
            self.reaction_roles_storage.watched_message_ids
            if len(self.reaction_roles_storage.watched_message_ids) > 0
            else await self.reaction_roles_storage.list_watched_message_ids()
        )

        if str(payload.message_id) not in watched_message_ids:
            return False

        log.info(
            f"Handling reaction role request - {payload.emoji} on {payload.message_id} from {payload.member}"
        )

        reaction_role = await self.reaction_roles_storage.get_reaction_role(
            server_id=str(payload.guild_id),
            msg_id=str(payload.message_id),
            reaction=payload.emoji.name,
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
