"""The abstraction interface for member_storage."""
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Member


class MemberStorageABC(ABC):
    @abstractmethod
    async def get_member(
        self, record_id: int, session: AsyncSession
    ) -> Optional[Member]:
        """Get a member by a record id.

        Parameters
        ----------
        record_id : int
            The id of the member
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[Member]
            The member object, if found.
        """
        ...

    @abstractmethod
    async def add_member(self, member: Member, session: AsyncSession) -> Member:
        """Add a member to the database.

        Parameters
        ----------
        member : Member
            The member object to add to the database.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Member
            The member object returned from the databse.
        """
        ...

    @abstractmethod
    async def list_members(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[Member]]:
        """List members that match a given filter.

        Parameters
        ----------
        *filters : ClauseElement
            A list of queries that members must match.
        session : AsyncSession
            The session to be used

        Returns
        -------
        Optional[List[Member]]
            A list of members that matched the supplied filter, if any.
        """
        ...

    @abstractmethod
    async def delete_member(self, member: Member, session: AsyncSession) -> None:
        """Deletes the member with the given discord id.

        Parameters
        ----------
        member : Member
            The member to be deleted
        session : AsyncSession
            The session to be used
        """
        ...

    @abstractmethod
    async def update_member(
        self, member: Member, session: AsyncSession, fields: Optional[List[str]] = None
    ) -> Member:
        """Update the specified fields of a member.

        Parameters
        ----------
        member : Member
            The member to update
        fields : Optional[List[str]], optional
            The optional list of filters to update.  If None, updates full model, by default None
        session : AsyncSession
            The session to be used

        Returns
        -------
        Member
            The updated member object.
        """
        ...
