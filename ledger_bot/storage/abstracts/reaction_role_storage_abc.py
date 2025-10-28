"""The abstraction interface for reaction_role_storage."""

from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import ReactionRole


class ReactionRoleStorageABC(ABC):
    @abstractmethod
    async def get_reaction_role(
        self, record_id: int, session: AsyncSession
    ) -> Optional[ReactionRole]:
        """Get a reaction_role by a record id.

        Parameters
        ----------
        record_id : int
            The id of the member
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[ReactionRole]
            The reaction_role object, if found.
        """
        ...

    @abstractmethod
    async def add_reaction_role(
        self, reaction_role: ReactionRole, session: AsyncSession
    ) -> ReactionRole:
        """Add a reaction_role to the database.

        Parameters
        ----------
        reaction_role : ReactionRole
            The reaction_role object to add to the database.
        session : AsyncSession
            The session to be used

        Returns
        -------
        ReactionRole
            The reaction_role object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_reeaction_roles(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[ReactionRole]]:
        """List reaction_roles that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that reaction_roles must match.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[List[ReactionRole]]
            A list of reaction_roles that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_reaction_role(
        self, reaction_role: ReactionRole, session: AsyncSession
    ) -> None:
        """Deletes the reaction_role with the given record id.

        Parameters
        ----------
        reaction_role : ReactionRole
            The member to be deleted
        session : AsyncSession
            The session to be used
        """
        ...

    @abstractmethod
    async def update_reaction_role(
        self,
        reaction_role: ReactionRole,
        session: AsyncSession,
        fields: Optional[List[str]] = None,
    ) -> ReactionRole:
        """Update the specified fields of a reaction_role.

        Parameters
        ----------
        reaction_role : ReactionRole
            The reaction_role to update
        fields : Optional[List[str]], optional
            The optional list of filters to update.  If None, updates full model, by default None
        session : AsyncSession
            The session to be used

        Returns
        -------
        ReactionRole
            The updated reaction_role object.
        """
        ...

    @abstractmethod
    async def list_watched_message_ids(self, session: AsyncSession) -> set[int]:
        """List message_ids that have reaction_roles.

        Parameters
        ----------
        session : AsyncSession
            The session to be used

        Returns
        -------
        set[int]
            A set containing message_ids
        """
        ...
