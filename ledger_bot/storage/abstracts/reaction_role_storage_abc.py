"""The abstraction interface for reaction_role_storage."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.sql import ColumnElement

from ledger_bot.models import ReactionRole


class ReactionRoleStorageABC(ABC):
    @abstractmethod
    async def get_reaction_role(self, record_id: int) -> Optional[ReactionRole]:
        """Get a reaction_role by a record id.

        Parameters
        ----------
        record_id : int
            The id of the member

        Returns
        -------
        Optional[ReactionRole]
            The reaction_role object, if found.
        """
        ...

    @abstractmethod
    async def add_reaction_role(self, reaction_role: ReactionRole) -> ReactionRole:
        """Add a reaction_role to the database.

        Parameters
        ----------
        reaction_role : ReactionRole
            The reaction_role object to add to the database.

        Returns
        -------
        ReactionRole
            The reaction_role object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_reeaction_roles(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[ReactionRole]]:
        """List reaction_roles that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that reaction_roles must match.

        Returns
        -------
        Optional[List[ReactionRole]]
            A list of reaction_roles that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_reaction_role(self, reaction_role: ReactionRole) -> None:
        """Deletes the reaction_role with the given record id.

        Parameters
        ----------
        reaction_role : ReactionRole
            The member to be deleted
        """
        ...

    @abstractmethod
    async def update_reaction_role(
        self, reaction_role: ReactionRole, fields: Optional[List[str]] = None
    ) -> ReactionRole:
        """Update the specified fields of a reaction_role.

        Parameters
        ----------
        reaction_role : ReactionRole
            The reaction_role to update
        fields : Optional[List[str]], optional
            The optional list of filters to update.  If None, updates full model, by default None

        Returns
        -------
        ReactionRole
            The updated reaction_role object.
        """
        ...

    @abstractmethod
    async def list_watched_message_ids(self) -> set[int]:
        """List message_ids that have reaction_roles.

        Returns
        -------
        set[int]
            A set containing message_ids
        """
        ...
