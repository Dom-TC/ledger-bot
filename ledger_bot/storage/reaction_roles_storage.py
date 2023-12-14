"""Class to interface with the Reaction Roles tables."""

import asyncio
import logging
from typing import List

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

    def list_reaction_roles():
        return NotImplementedError

    def get_reaction_role():
        return NotImplementedError
