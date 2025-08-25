"""The abstraction interface for member_storage."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Member


class MemberStorageABC(ABC):
    @abstractmethod
    async def get_member(self, record_id: int) -> Optional[Member]:
        """Get a member by a record id.

        Parameters
        ----------
        record_id : int
            The id of the member

        Returns
        -------
        Optional[Member]
            The member object, if found.
        """
        ...

    @abstractmethod
    async def add_member(self, member: Member) -> Member:
        """Add a member to the database.

        Parameters
        ----------
        member : Member
            The member object to add to the database.

        Returns
        -------
        Member
            The member object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_members(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[Member]]:
        """List members that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that members must match.

        Returns
        -------
        Optional[List[Member]]
            A list of members that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_member(self, member: Member) -> None:
        """Deletes the member with the given discord id.

        Parameters
        ----------
        member : Member
            The member to be deleted
        """
        ...

    @abstractmethod
    async def update_member(
        self, member: Member, fields: Optional[List[str]] = None
    ) -> Member:
        """Update the specified fields of a member.

        Parameters
        ----------
        member : Member
            The member to update
        fields : Optional[List[str]], optional
            The optional list of filters to update.  If None, updates full model, by default None

        Returns
        -------
        Member
            The updated member object.
        """
        ...
