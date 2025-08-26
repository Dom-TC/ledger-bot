"""A service to provide interfacing for MemberStorage."""

import logging
from typing import List, Optional

from asyncache import cached
from cachetools import LRUCache
from discord import Member as DiscordMember
from discord import User as DiscordUser

from ledger_bot.models import Member
from ledger_bot.storage import MemberStorage

log = logging.getLogger(__name__)


class MemberService:
    def __init__(self, member_storage: MemberStorage, bot_id: str):
        self.member_storage = member_storage
        self.bot_id = bot_id

    async def get_member_from_record_id(self, record_id: int) -> Optional[Member]:
        """Get a member with the given record_id.

        Parameters
        ----------
        record_id : int
            The id of the record being retrieved

        Returns
        -------
        Optional[Member]
            The Member object
        """
        reminder = await self.member_storage.get_member(record_id=record_id)
        return reminder

    @cached(LRUCache(maxsize=64))
    async def get_or_add_member(
        self, discord_member: DiscordMember | DiscordUser
    ) -> Member:
        """Fetches an existing member or adds a new record for them.

        Parameters
        ----------
        discord_member : DiscordMember
            The discord Member object

        Returns
        -------
        Member
            The record from the database for this member
        """
        members = await self.member_storage.list_members(
            Member.discord_id == discord_member.id
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
                nickname=discord_member.nick
                if type(discord_member) is DiscordMember
                else None,
                bot_id=self.bot_id,
            )

            member_record = await self.member_storage.add_member(member=member_object)
        return member_record

    async def list_all_members(self) -> List[Member]:
        """Get a list of all members.

        Returns
        -------
        List[Member]
            All the members in the database, empty if none exist
        """
        log.info("Listing all members")
        member_list = await self.member_storage.list_members()

        # If no members found, return an empty list rather than None
        if not member_list:
            member_list = []

        log.info(f"Found {len(member_list)} members")

        return member_list

    async def set_dietary_requirement(
        self, discord_member: DiscordMember, requirement: str
    ) -> Member:
        """Set the dietary requirement for the given discord user.

        Parameters
        ----------
        discord_member : DiscordMember
            The discord member
        requirement : str
            The dietary requirement

        Returns
        -------
        Member
            The updated member object
        """
        member = await self.get_or_add_member(discord_member)

        member.dietary_requirements = requirement

        updated_member = await self.member_storage.update_member(
            member, fields=["dietary_requirements"]
        )

        log.info(
            f"Updated dietary_requirements for member {member.id} ({member.username}) to '{requirement}'"
        )
        return updated_member
