"""SQLite implementation of ReactionRoleStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import ReactionRole

from .abstracts import ReactionRoleStorageABC

log = logging.getLogger(__name__)


class ReactionRoleStorage(ReactionRoleStorageABC):
    """SQLite implementation of ReactionRoleStorageABC."""

    def __init__(self, session_factory: sessionmaker):
        """Initialise ReactionRoleStorage.

        Parameters
        ----------
        session_factory : Callable[[], AsyncSession]
            Factory to produce new SQLAlchemy AsyncSession objects.
        """
        self._session_factory = session_factory

    async def get_reaction_role(self, record_id: int) -> Optional[ReactionRole]:
        async with self._session_factory() as session:
            log.info(f"Getting reaction_role with record_id {record_id}")
            result = await session.get(ReactionRole, record_id)
            return result

    async def add_reaction_role(self, reaction_role: ReactionRole) -> ReactionRole:
        async with self._session_factory() as session:
            log.info(f"Adding reaction_role for {reaction_role.role_name}")
            session.add(reaction_role)
            await session.commit()
            await session.refresh(reaction_role)
            log.info(f"Reaction_Role added with id {reaction_role.id}")
            return reaction_role

    async def list_reeaction_roles(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[ReactionRole]]:
        async with self._session_factory() as session:
            log.info(f"Listing reaction_roles that match query {filters}")
            query = select(ReactionRole)
            if filters:
                query = query.where(*filters)
            result = await session.execute(query)
            reaction_roles = result.scalars().all()
            log.info(f"Found {len(reaction_roles)} reminders")
            return reaction_roles if reaction_roles else None

    async def delete_reaction_role(self, reaction_role: ReactionRole) -> None:
        async with self._session_factory() as session:
            log.info(
                f"Deleting reaction_role id {reaction_role.id} ({reaction_role.role_name})"
            )
            await session.delete(reaction_role)
            await session.commit()

    async def update_reaction_role(
        self, reaction_role: ReactionRole, fields: Optional[List[str]] = None
    ) -> ReactionRole:
        async with self._session_factory() as session:
            # Attach the reaction_role object to the session
            db_reaction_role = await session.merge(reaction_role)

            if fields:
                # Only update the specified fields
                for field in fields:
                    setattr(db_reaction_role, field, getattr(reaction_role, field))
                log.info(
                    f"Updating reaction_role {db_reaction_role.id} fields: {fields}"
                )
            else:
                # Full update: merge already updates all fields
                log.info(f"Updating all fields for reaction_role {db_reaction_role.id}")

            await session.commit()
            await session.refresh(db_reaction_role)
            return db_reaction_role

    async def list_watched_message_ids(self) -> set[int]:
        async with self._session_factory() as session:
            log.info("Listing watched message ids")
            message_ids = session.scalars(select(ReactionRole.message_id))
            return set(message_ids)
