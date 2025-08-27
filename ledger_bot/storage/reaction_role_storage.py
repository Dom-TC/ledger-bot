"""SQLite implementation of ReactionRoleStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import ReactionRole

from .abstracts import ReactionRoleStorageABC

log = logging.getLogger(__name__)


class ReactionRoleStorage(ReactionRoleStorageABC):
    """SQLite implementation of ReactionRoleStorageABC."""

    async def get_reaction_role(
        self, record_id: int, session: AsyncSession
    ) -> Optional[ReactionRole]:
        log.info(f"Getting reaction_role with record_id {record_id}")
        result: ReactionRole | None = await session.get(ReactionRole, record_id)
        return result

    async def add_reaction_role(
        self, reaction_role: ReactionRole, session: AsyncSession
    ) -> ReactionRole:
        log.info(f"Adding reaction_role for {reaction_role.role_name}")
        session.add(reaction_role)
        await session.flush()
        await session.refresh(reaction_role)
        log.info(f"Reaction_Role added with id {reaction_role.id}")
        return reaction_role

    async def list_reeaction_roles(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[ReactionRole]]:
        log.info(f"Listing reaction_roles that match query {filters}")
        query = select(ReactionRole)
        if filters:
            query = query.where(*filters)
        result = await session.execute(query)
        reaction_roles = list(result.scalars().all())
        log.info(f"Found {len(reaction_roles)} reminders")
        return reaction_roles if reaction_roles else None

    async def delete_reaction_role(
        self, reaction_role: ReactionRole, session: AsyncSession
    ) -> None:
        log.info(
            f"Deleting reaction_role id {reaction_role.id} ({reaction_role.role_name})"
        )
        await session.delete(reaction_role)
        await session.flush()

    async def update_reaction_role(
        self,
        reaction_role: ReactionRole,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> ReactionRole:
        # Attach the reaction_role object to the session
        db_reaction_role: ReactionRole = await session.merge(reaction_role)

        if fields:
            # Only update the specified fields
            for field in fields:
                setattr(db_reaction_role, field, getattr(reaction_role, field))
            log.info(f"Updating reaction_role {db_reaction_role.id} fields: {fields}")
        else:
            # Full update: merge already updates all fields
            log.info(f"Updating all fields for reaction_role {db_reaction_role.id}")

        await session.flush()
        await session.refresh(db_reaction_role)
        return db_reaction_role

    async def list_watched_message_ids(self, session: AsyncSession) -> set[int]:
        log.info("Listing watched message ids")
        message_ids = await session.scalars(select(ReactionRole.message_id))
        return set(message_ids)
