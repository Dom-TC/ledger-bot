"""Class to interface with the Reaction Roles tables."""

import asyncio
import logging
from typing import Dict, List, Optional

from aiohttp import ClientSession
from asyncache import cached
from cachetools import LRUCache

from ledger_bot.models import ReactionRole

from .base_storage import BaseStorage

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

    async def list_watched_message_ids(self) -> List[str]:
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
        return reaction_role_entries

    async def _list_reaction_roles(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ) -> List[Dict[str, str | List[str]]]:
        log.debug(f"Filter: {filter_by_formula}")
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
