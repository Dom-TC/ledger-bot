"""Mixin for dealing with the Members table."""

import logging
from typing import List, Optional

from aiohttp import ClientSession
from asyncache import cached
from cachetools import LRUCache
from discord import Member as DiscordMember

from ledger_bot.models import Member

from .base_storage import BaseStorage

log = logging.getLogger(__name__)


class MembersMixin(BaseStorage):
    members_url: str
    bot_id: str

    async def _list_members(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ):
        return await self._list(self.members_url, filter_by_formula, session)

    def _list_all_members(
        self,
        filter_by_formula: str,
        sort: List[str],
        session: Optional[ClientSession] = None,
    ):
        return self._iterate(
            self.members_url,
            filter_by_formula=filter_by_formula,
            sort=sort,
            session=session,
        )

    async def _find_member_by_discord_id(
        self, discord_id: str, session: Optional[ClientSession] = None
    ):
        log.debug(f"Finding member {discord_id}")
        members = await self._list_members(
            filter_by_formula="{{discord_id}}={value}".format(value=discord_id),
            session=session,
        )
        return members[0] if members else None

    async def _retrieve_member(
        self, member_id: str, session: Optional[ClientSession] = None
    ):
        return await self._get(f"{self.members_url}/{member_id}", session=session)

    async def _delete_members(
        self, members: List[str], session: ClientSession | None = None
    ):
        # AirTable API only allows us to batch delete 10 records at a time, so we need to split up requests
        member_ids_length = len(members)
        delete_batches = (
            members[offset : offset + 10] for offset in range(0, member_ids_length, 10)
        )

        for records_to_delete in delete_batches:
            await self._delete(self.members_url, records_to_delete, session)

    async def insert_member(
        self, record: dict, session: Optional[ClientSession] = None
    ) -> dict:
        """
        Inserts a member into the table.

        Paramaters
        ----------
        record : dict
            The record to insert

        session : ClientSession, optional
            The ClientSession to use

        Returns
        -------
        dict
            A Dictionary containing the inserted record
        """
        return await self._insert(self.members_url, record, session)

    @cached(LRUCache(maxsize=64))
    async def get_or_add_member(self, member: DiscordMember) -> Member:
        """
        Fetches an existing member or adds a new record for them.

        Paramaters
        ----------
        member : DiscordMember
            The member

        Returns
        -------
        Member
            The record from AirTable for this member
        """
        member_record = await self._find_member_by_discord_id(str(member.id))

        if not member_record:
            data = {
                "username": member.name,
                "discord_id": str(member.id),
                "nickname": member.nick,
                "bot_id": self.bot_id or "",
            }
            member_record = await self.insert_member(data)
            log.debug(
                f"Added {member_record['fields']['username']} ({member_record['fields']['discord_id']}) to AirTable"
            )
        return Member.from_airtable(member_record)

    @cached(LRUCache(maxsize=64))
    async def get_member_from_record_id(self, record_id: str) -> Member:
        """Returns the member object for the member with a given AirTable record id."""
        log.info(f"Finding member with record {record_id}")
        member_record = await self._retrieve_member(record_id)
        return Member.from_airtable(member_record)
