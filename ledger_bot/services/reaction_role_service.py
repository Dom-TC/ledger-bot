"""A service to provide interfacing for ReactionRoleStorage."""

import logging
from typing import List

from asyncache import cached
from cachetools import LRUCache
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.models import ReactionRole
from ledger_bot.storage import ReactionRoleStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class ReactionRoleService(ServiceHelpers):
    def __init__(
        self,
        reaction_role_storage: ReactionRoleStorage,
        bot_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.reaction_role_storage = reaction_role_storage
        self.watched_message_ids: set[int] = set()
        self.bot_id = bot_id

        super().__init__(session_factory)

    async def get_reaction_role(
        self, record_id: int, session: AsyncSession | None = None
    ) -> ReactionRole | None:
        """Get a ReactionRole with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved

        Returns
        -------
        Optional[ReactionRole]
            The ReactionRole object
        """
        async with self._get_session(session) as session:
            reminder = await self.reaction_role_storage.get_reaction_role(
                record_id=record_id, session=session
            )
            return reminder

    @cached(LRUCache(maxsize=64))
    async def get_reaction_role_by_role_id(
        self, server_id: int, role_id: int, session: AsyncSession | None = None
    ) -> ReactionRole | None:
        """Get the reaction role for a given role id.

        Parameters
        ----------
        server_id : int
            The id of the server the role is in
        role_id : int
            The id of the role

        Returns
        -------
        Optional[ReactionRole]
            The ReactionRole object
        """
        log.debug(f"Finding ReactionRole with role {role_id} in server {server_id}")

        async with self._get_session(session) as session:
            filter_ = and_(
                ReactionRole.server_id == server_id, ReactionRole.role_id == role_id
            )

            reaction_role = await self.reaction_role_storage.list_reeaction_roles(
                filter_, session=session
            )

            log.debug(f"Found reaction roles: {reaction_role}")
            return reaction_role[0] if reaction_role else None

    @cached(LRUCache(maxsize=64))
    async def get_reaction_role_by_reaction(
        self,
        server_id: int,
        message_id: int,
        reaction: str,
        session: AsyncSession | None = None,
    ) -> ReactionRole | None:
        """Get the reaction role for a given reaction.

        Parameters
        ----------
        server_id : int
            The id of the server the role is in
        message_id : int
            The id of the message the reaction was added to
        reaction : str
            The reaction being looked up

        Returns
        -------
        ReactionRole
            The reaction role
        """
        log.debug(
            f"Finding ReactionRole with reaction {reaction} on message {message_id} in server {server_id}"
        )

        reaction_bytecode = reaction.encode("unicode-escape").decode("ASCII")

        async with self._get_session(session) as session:
            filter_ = and_(
                ReactionRole.server_id == server_id,
                ReactionRole.message_id == message_id,
                or_(
                    ReactionRole.reaction_name == reaction,
                    ReactionRole.reaction_bytecode == reaction_bytecode,
                ),
            )

            reaction_role = await self.reaction_role_storage.list_reeaction_roles(
                filter_, session=session
            )

            log.debug(f"Found reaction roles: {reaction_role}")
            return reaction_role[0] if reaction_role else None

    async def save_reaction_role(
        self,
        reaction_role: ReactionRole,
        fields: List[str] | None = None,
        session: AsyncSession | None = None,
    ) -> ReactionRole:
        """Saves the provided ReactionRole.

        If it has no primary key, inserts a new instance, otherwise updates the old instance.
        If a list of fields are specified, only updates those fields.

        Paramaters
        ----------
        reaction_role: ReactionRole
            The ReactionRole to insert

        fields : Optional
            The fields to save / update

        Returns
        -------
        ReactionRole
            The saved ReactionRole object
        """
        log.info(
            f"Saving reaction {reaction_role.reaction_name} for role {reaction_role.role_name}"
        )
        reaction_role.bot_id = self.bot_id

        async with self._get_session(session) as session:
            if reaction_role.id:
                log.info(f"ReactionRole already has id {reaction_role.id}. Updating...")

                if fields:
                    if "bot_id" not in fields:
                        fields.append("bot_id")
                    log.info(f"Only updating fields: {fields}")

                reaction_role = await self.reaction_role_storage.update_reaction_role(
                    reaction_role=reaction_role, fields=fields, session=session
                )
                await session.commit()
            else:
                log.info("ReactionRole doesn't exist. Adding...")
                reaction_role = await self.reaction_role_storage.add_reaction_role(
                    reaction_role=reaction_role, session=session
                )
                await session.commit()

            log.info(f"ReactionRole saved with id {reaction_role.id}")
            return reaction_role

    async def delete_reaction_role(
        self, reaction_role: ReactionRole, session: AsyncSession | None = None
    ) -> None:
        """Delete the specified ReactionRole.

        Parameters
        ----------
        reaction_role: ReactionRole
            The ReactionRole to be deleted
        """
        log.info(f"Deleting ReactionRole {reaction_role.id}")
        async with self._get_session(session) as session:
            await self.reaction_role_storage.delete_reaction_role(
                reaction_role, session=session
            )
            await session.commit()

    async def list_watched_message_ids(
        self, session: AsyncSession | None = None
    ) -> set[int]:
        """List all the message ids that are being monitored for reactions.

        Returns
        -------
        set[int]
            The message ideas
        """
        async with self._get_session(session) as session:
            watched_message_ids = (
                await self.reaction_role_storage.list_watched_message_ids(
                    session=session
                )
            )

            log.info(
                f"Found {len(watched_message_ids)} messages to watch: {watched_message_ids}"
            )

            self.watched_message_ids = set(watched_message_ids)
            return watched_message_ids
