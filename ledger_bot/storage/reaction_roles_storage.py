"""Class to interface with the Reaction Roles tables."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession
from asyncache import cached
from cachetools import LRUCache

from ledger_bot.models import ReactionRole

from .mixins import BaseStorage

log = logging.getLogger(__name__)


class ReactionRolesStorage(BaseStorage):
    def __init__(
        self,
        airtable_base: str,
        airtable_key: str,
        bot_id: str,
    ):
        super().__init__(airtable_base, airtable_key)
        self.bot_id = bot_id
        self.reaction_role_url = (
            f"https://api.airtable.com/v0/{airtable_base}/reaction_roles"
        )
        self.watched_message_ids: set[str] = set()
        self.reaction_roles_lock = asyncio.Lock()

    async def list_watched_message_ids(self) -> set[str]:
        log.debug("Listing watched message ids")
        async with self.reaction_roles_lock:
            reaction_roles_iterator = self._iterate(
                self.reaction_role_url,
                filter_by_formula=None,
                fields="message_id",
            )
            reaction_role_entries = [
                reaction_role["fields"]["message_id"]
                async for reaction_role in reaction_roles_iterator
            ]
            self.watched_message_ids = set(reaction_role_entries)
        return set(reaction_role_entries)

    async def _list_reaction_roles(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ) -> List[Dict[str, str | List[str]]]:
        return await self._list(self.reaction_role_url, filter_by_formula, session)

    @cached(LRUCache(maxsize=64))
    async def get_reaction_role(
        self,
        server_id: str,
        msg_id: str,
        reaction: str,
        session: Optional[ClientSession] = None,
    ) -> ReactionRole | None:
        log.debug(
            f"Finding reaction_role with guild {server_id}, message_id {msg_id}, and emoji {reaction}"
        )
        raw_reaction_role = await self._list_reaction_roles(
            filter_by_formula=f'AND(server_id={server_id},message_id={msg_id},reaction_name="{reaction}")',
            session=session,
        )

        log.debug(f"raw_reaction_role: {raw_reaction_role}")

        if len(raw_reaction_role) > 0:
            return ReactionRole.from_airtable(raw_reaction_role[0])
        else:
            return None

    async def find_reaction_role_by_role_id(
        self, server_id: int, role_id: int, session: Optional[ClientSession] = None
    ) -> ReactionRole | None:
        log.debug(f"Finding ReactionRole with role {role_id}")

        raw_reaction_role = await self._list_reaction_roles(
            filter_by_formula=f"AND(server_id={server_id},role_id={role_id})",
            session=session,
        )

        log.debug(f"raw_reaction_role: {raw_reaction_role}")
        return (
            ReactionRole.from_airtable(raw_reaction_role[0])
            if raw_reaction_role
            else None
        )

    async def find_reaction_role_by_reaction(
        self, server_id: int, reaction: str, session: Optional[ClientSession] = None
    ) -> ReactionRole | None:
        log.debug(f"Finding ReactionRole with reaction {reaction}")

        raw_reaction_role = await self._list_reaction_roles(
            filter_by_formula=f'AND(server_id={server_id},reaction_name="{reaction}")',
            session=session,
        )

        log.debug(f"raw_reaction_role: {raw_reaction_role}")
        return (
            ReactionRole.from_airtable(raw_reaction_role[0])
            if raw_reaction_role
            else None
        )

    async def insert_reaction_role(
        self, record: Dict[str, Any], session: Optional[ClientSession] = None
    ) -> ReactionRole:
        result = await self._insert(self.reaction_role_url, record, session)
        return ReactionRole.from_airtable(result)

    async def update_reaction_role(
        self,
        record_id: str,
        reaction_role_record: Dict[str, Any],
        session: Optional[ClientSession] = None,
    ) -> ReactionRole:
        result = await self._update(
            self.reaction_role_url + "/" + record_id, reaction_role_record, session
        )
        return ReactionRole.from_airtable(result)

    async def save_reaction_role(
        self, reaction_role: ReactionRole, fields: List[str] | None = None
    ) -> ReactionRole:
        log.debug(f"reaction_role: {reaction_role}")

        fields = fields or [
            "server_id",
            "message_id",
            "reaction_name",
            "role_id",
            "role_name",
            "bot_id",
        ]

        # Always store bot_id
        reaction_role.bot_id = self.bot_id or ""
        if "bot_id" not in fields:
            fields.append("bot_id")

        reaction_role_data = reaction_role.to_airtable(fields=fields)
        log.info(f"Adding reaction role data: {reaction_role_data['fields']}")
        if reaction_role.record_id:
            log.info(f"Updating transaction with id: {reaction_role_data['id']}")
            return await self.update_reaction_role(
                record_id=reaction_role_data["id"],
                reaction_role_record=reaction_role_data["fields"],
            )
        else:
            log.info("Adding transaction to Airtable")
            return await self.insert_reaction_role(record=reaction_role_data["fields"])
