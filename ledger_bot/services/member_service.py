"""A service to provide interfacing for MemberStorage."""

import logging
from typing import List

from asyncache import cached
from cachetools import LRUCache
from discord import Member as DiscordMember
from discord import User as DiscordUser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.models import Member, MemberTransactionSummary
from ledger_bot.storage import MemberStorage
from ledger_bot.utils import is_valid_timezone, resolve_timezone

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class MemberService(ServiceHelpers):
    def __init__(
        self,
        member_storage: MemberStorage,
        bot_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.member_storage = member_storage
        self.bot_id = bot_id

        super().__init__(session_factory)

    async def get_member_from_record_id(
        self, record_id: int, session: AsyncSession | None = None
    ) -> Member | None:
        """Get a member with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Optional[Member]
            The Member object
        """
        async with self._get_session(session) as session:
            member = await self.member_storage.get_member(
                record_id=record_id, session=session
            )
            return member

    @cached(LRUCache(maxsize=64))
    async def get_or_add_member(
        self,
        discord_member: DiscordMember | DiscordUser,
        session: AsyncSession | None = None,
    ) -> Member:
        """Fetches an existing member or adds a new record for them.

        Parameters
        ----------
        discord_member : DiscordMember
            The discord Member object
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Member
            The record from the database for this member
        """
        async with self._get_session(session) as session:
            members = await self.member_storage.list_members(
                Member.discord_id == discord_member.id, session=session
            )
            if members:
                member_record = members[0]
                log.debug(
                    f"Found member record {member_record.id} {member_record.username} {member_record.discord_id}"
                )
            else:
                member_object = Member(
                    username=discord_member.name,
                    discord_id=discord_member.id,
                    nickname=(
                        discord_member.nick
                        if type(discord_member) is DiscordMember
                        else None
                    ),
                    bot_id=self.bot_id,
                )

                member_record = await self.member_storage.add_member(
                    member=member_object, session=session
                )
                await session.commit()
            return member_record

    async def list_all_members(
        self, session: AsyncSession | None = None
    ) -> List[Member]:
        """Get a list of all members.

        Parameters
        ----------
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        List[Member]
            All the members in the database, empty if none exist
        """
        async with self._get_session(session) as session:
            log.info("Listing all members")
            member_list = await self.member_storage.list_members(session=session)

            # If no members found, return an empty list rather than None
            if not member_list:
                member_list = []

            log.info(f"Found {len(member_list)} members")

            return member_list

    async def set_dietary_requirement(
        self,
        discord_member: DiscordMember,
        requirement: str,
        session: AsyncSession | None = None,
    ) -> Member:
        """Set the dietary requirement for the given discord user.

        Parameters
        ----------
        discord_member : DiscordMember
            The discord member
        requirement : str
            The dietary requirement
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Member
            The updated member object
        """
        async with self._get_session(session) as session:
            member = await self.get_or_add_member(discord_member, session=session)

            member.dietary_requirements = requirement

            updated_member = await self.member_storage.update_member(
                member, fields=["dietary_requirements"], session=session
            )

            await session.commit()

            log.info(
                f"Updated dietary_requirements for member {member.id} ({member.username}) to '{requirement}'"
            )
            return updated_member

    async def set_timezone(
        self,
        discord_member: DiscordMember,
        timezone: str,
        session: AsyncSession | None = None,
    ) -> Member:
        """Set the timezone for the given discord user.

        Parameters
        ----------
        discord_member : DiscordMember
            The discord member
        timezone : str
            The users timezone
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Member
            The updated member object
        """
        async with self._get_session(session) as session:
            # I don't know why we have to specify type Member here
            # self.get_or_add_member is set to return Member
            # VSCode doesn't complain but mypy does, for some reason
            # So here we are
            member: Member = await self.get_or_add_member(
                discord_member, session=session
            )

            if not is_valid_timezone(timezone):
                log.info(f"Invalid timezone: {timezone}")
                return member

            if resolve_timezone(timezone):
                member.timezone = timezone
            else:
                log.error(f"Failed to resolve timezone {timezone}")
                return member

            updated_member = await self.member_storage.update_member(
                member, fields=["timezone"], session=session
            )

            await session.commit()

            log.info(
                f"Updated timezone for member {member.id} ({member.username}) to '{timezone}'"
            )
            return updated_member

    async def get_member_transaction_summary(
        self, member: Member, session: AsyncSession | None = None
    ) -> MemberTransactionSummary:
        async with self._get_session(session) as session:
            return await self.member_storage.get_transaction_summary(
                member, session=session
            )

    async def update_member(
        self,
        member: Member,
        fields: List[str] | None = None,
        session: AsyncSession | None = None,
    ) -> Member:
        """Update a member.

        Parameters
        ----------
        member: Member
            The member
        fields: List[str] | None, optional
            If provided only the updated fields will be updated
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Member
            The updated member object
        """
        async with self._get_session(session) as session:
            updated_member = await self.member_storage.update_member(
                member, fields=fields, session=session
            )

            await session.commit()

            log.info(f"Updated member {member.id} ({member.username})")
            return updated_member
