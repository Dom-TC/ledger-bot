"""The various models used by ledger-bot."""

import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Literal, Optional, Union

import discord
from aiohttp import ClientSession
from discord import Member as DiscordMember

from .models import AirTableError, BotMessage, Member, Transaction

log = logging.getLogger(__name__)


async def run_request(
    action_to_run: Callable[[ClientSession], Awaitable[dict]],
    session: Optional[ClientSession] = None,
):
    """
    Asynchronously run requests reusing sessions provided.

    Paramaters
    ----------
    action_to_run : Callable
        The request that will be run

    session : ClientSession, optional
        The session to use, if provided
    """
    if not session:
        async with ClientSession() as new_session:
            return await action_to_run(new_session)
    else:
        return await action_to_run(session)


async def airtable_sleep():
    """Sleep to meet AirTable's rate limits (5 requests per second)."""
    await asyncio.sleep(1.0 / 5)


class AirtableStorage:
    """
    A class to interface with AirTable.

    Attributes
    ----------
    airtable_key : str
        The authentication key to connect to the base
    bot_id : str
        The id of ledger-bot
    users_url : str
        The endpoint for the users table
    wines_url : str
        The endpoint for the wines table
    bot_messages_url : str
        The endpoint for the bot_messages table
    auth_header :
        The authentication header

    Methods
    -------
    insert_member(record, session)
        Creates a new member entry

    get_or_add_member(member)
        Either returns the record for the given member, or creates an entry and returns that

    insert_transaction(record, session)
        Creates a new transaction entry

    """

    def __init__(
        self,
        airtable_base: str,
        airtable_key: str,
        bot_id: Optional[str],
    ):
        self.airtable_key = airtable_key
        self.bot_id = bot_id
        self.members_url = f"https://api.airtable.com/v0/{airtable_base}/members"
        self.wines_url = f"https://api.airtable.com/v0/{airtable_base}/wines"
        self.bot_messages_url = (
            f"https://api.airtable.com/v0/{airtable_base}/bot_messages"
        )
        self.auth_header = {"Authorization": f"Bearer {self.airtable_key}"}
        self._semaphore = asyncio.Semaphore(5)

    async def _get(
        self,
        url: str,
        params: Optional[dict[str, str]] = None,
        session: Optional[ClientSession] = None,
    ):
        async def run_fetch(session_to_use: ClientSession):
            async with session_to_use.get(
                url,
                params=params,
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    print(r.url)
                    raise AirTableError(r.url, await r.json())
                response: dict = await r.json()
                return response

        async with self._semaphore:
            result = await run_request(run_fetch, session)
            await airtable_sleep()
            return result

    async def _list(
        self,
        base_url: str,
        filter_by_formula: Optional[str],
        session: Optional[ClientSession] = None,
        view: Optional[str] = None,
    ):
        params = {}
        if filter_by_formula := filter_by_formula:
            params.update({"filterByFormula": filter_by_formula})
        if view := view:
            params.update({"view": view})
        response = await self._get(base_url, params, session)
        return response.get("records", [])

    async def _iterate(
        self,
        base_url: str,
        filter_by_formula: str,
        sort: Optional[list[str]] = None,
        session: Optional[ClientSession] = None,
    ):
        params = {"filterByFormula": filter_by_formula}
        if sort:
            for idx, field in enumerate(sort):
                params.update({"sort[{index}][field]".format(index=idx): field})
                params.update({"sort[{index}][direction]".format(index=idx): "desc"})
        offset = None
        while True:
            if offset:
                params.update(offset=offset)
            async with self._semaphore:
                response = await self._get(base_url, params, session)
                await airtable_sleep()
            records = response.get("records", [])
            for record in records:
                yield record
            offset = response.get("offset")
            if not offset:
                break

    async def _delete(
        self,
        base_url: str,
        records_to_delete: [str],
        session: Optional[ClientSession] = None,
    ):
        async def run_delete(session_to_use: ClientSession):
            async with session_to_use.delete(
                (
                    base_url
                    if len(records_to_delete) > 1
                    else base_url + f"/{records_to_delete[0]}"
                ),
                params=(
                    {"records": records_to_delete}
                    if len(records_to_delete) > 1
                    else None
                ),
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    log.warning(f"Failed to delete IDs: {records_to_delete}")
                    raise AirTableError(r.url, await r.json())

        async with self._semaphore:
            result = await run_request(run_delete, session)
            await airtable_sleep()
            return result

    async def _modify(
        self,
        url: str,
        method: Literal["post", "patch"],
        record: dict,
        session: Optional[ClientSession] = None,
    ):
        async def run_insert(session_to_use: ClientSession):
            data = {"fields": record}
            async with session_to_use.request(
                method,
                url,
                json=data,
                headers=self.auth_header,
            ) as r:
                if r.status != 200:
                    raise AirTableError(r.url, await r.json())
                response: dict = await r.json()
                return response

        async with self._semaphore:
            result = await run_request(run_insert, session)
            await airtable_sleep()
            return result

    async def _insert(
        self, url: str, record: dict, session: Optional[ClientSession] = None
    ):
        return await self._modify(url, "post", record, session)

    async def _update(
        self, url: str, record: dict, session: Optional[ClientSession] = None
    ):
        return await self._modify(url, "patch", record, session)

    async def _list_members(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ):
        return await self._list(self.members_url, filter_by_formula, session)

    def _list_all_members(
        self,
        filter_by_formula: str,
        sort: [str],
        session: Optional[ClientSession] = None,
    ):
        return self._iterate(self.members_url, filter_by_formula, sort, session)

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

    async def _delete_members(self, members: [str], session: ClientSession = None):
        # AirTable API only allows us to batch delete 10 records at a time, so we need to split up requests
        member_ids_length = len(members)
        delete_batches = (
            members[offset : offset + 10] for offset in range(0, member_ids_length, 10)
        )

        for records_to_delete in delete_batches:
            await self._delete(self.motto_url, records_to_delete, session)

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
        member_record = await self._find_member_by_discord_id(member.id)

        if not member_record:
            data = {
                "username": member.name,
                "discord_id": str(member.id),
                "nickname": member.nick,
                "bot_id": self.bot_id or "",
            }
            member_record = await self.insert_member(data)
            log.debug(
                f"Added {member_record['fields']['username']} ({member_record['fields']['id']}) to AirTable"
            )
        return Member.from_airtable(member_record)

    async def get_member_from_record_id(self, record_id: int) -> Member:
        """Returns the member object for the member with a given AirTable record id."""
        log.info(f"Finding member with record {record_id}")
        member_record = await self._retrieve_member(record_id)
        return Member.from_airtable(member_record)

    async def insert_transaction(
        self, record: dict, session: Optional[ClientSession] = None
    ) -> dict:
        """
        Inserts a transaction into the table.

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
        return await self._insert(self.wines_url, record, session)

    async def update_transaction(
        self,
        record_id: str,
        transaction_record: dict,
        session: Optional[ClientSession] = None,
    ):
        """
        Updates a specific transaction record.

        Paramaters
        ----------
        record_id : str
            The primary key of the transaction to update

        transaction_record : dict
            The records to update

        session : ClientSession, optional
            The ClientSession to use

        """
        return await self._update(
            self.wines_url + "/" + record_id, transaction_record, session
        )

    async def save_transaction(self, transaction: Transaction, fields=None):
        """
        Saves the provided Transaction.

        If it has no primary key, inserts a new instance, otherwise updates the old instance.
        If a list of fields are specified, only saves/updates those fields.

        Paramaters
        ----------
        transaction : Transaction
            The transaction to insert

        fields : Optional
            The fields to save / update

        """
        fields = fields or [
            "seller_id",
            "buyer_id",
            "wine",
            "price",
            "sale_approved",
            "delivered",
            "paid",
            "cancelled",
            "creation_date",
            "approved_date",
            "paid_date",
            "delivered_date",
            "cancelled_date",
            "guild_id",
            "channel_id",
            "bot_message_id",
        ]

        # Always store bot_id
        transaction.bot_id = self.bot_id or ""
        if "bot_id" not in fields:
            fields.append("bot_id")

        transaction_data = transaction.to_airtable(fields=fields)
        log.info(f"Adding transaction data: {transaction_data['fields']}")
        if transaction.id:
            log.info(f"Updating transaction with id: {transaction_data['id']}")
            return await self.update_transaction(
                transaction_data["id"], transaction_data["fields"]
            )
        else:
            log.info("Adding transaction to Airtable")
            return await self.insert_transaction(transaction_data["fields"])

    async def _insert_bot_message(
        self, record: dict, session: Optional[ClientSession] = None
    ) -> dict:
        return await self._insert(self.bot_messages_url, record, session)

    async def record_bot_message(
        self,
        message: Union[discord.Message, discord.interactions.InteractionMessage],
        transaction: Transaction,
    ):
        """Create a record in bot_messages for a given bot_message.

        Paramaters
        ----------
        message : Union[discord.Message, discord.interactions.InteractionMessage]
            The message to store
        transaction : Transaction
            The transaction the message is referencing

        Returns
        -------
        dict
            A dictionary containing the inserted record
        """
        data = {
            "bot_message_id": str(message.id),
            "channel_id": str(message.channel.id),
            "guild_id": str(message.guild.id),
            "transaction_id": [transaction.id],
            "message_creation_date": datetime.datetime.utcnow().isoformat(),
            "bot_id": self.bot_id or "",
        }
        log.info(f"Storing bot_message: {data}")
        return await self._insert_bot_message(record=data)

    async def _list_bot_messages(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ):
        return await self._list(self.bot_messages_url, filter_by_formula, session)

    async def find_bot_message_by_message_id(
        self, bot_message_id: str, session: Optional[ClientSession] = None
    ):
        log.debug(f"Finding bot_message with id {bot_message_id}")
        bot_messages = await self._list_bot_messages(
            filter_by_formula="{{bot_message_id}}={value}".format(value=bot_message_id),
            session=session,
        )
        return bot_messages[0] if bot_messages else None

    async def _list_transactions(
        self, filter_by_formula: str, session: Optional[ClientSession] = None
    ):
        return await self._list(self.wines_url, filter_by_formula, session)

    async def _retrieve_transaction(
        self, transaction_id: str, session: Optional[ClientSession] = None
    ):
        log.debug(f"Retrieving transaction with id {transaction_id}")
        return await self._get(f"{self.wines_url}/{transaction_id}", session=session)

    async def find_transaction_by_bot_message_id(self, message_id: str) -> Transaction:
        """Takes a message and returns any associated Transactions, else returns None."""
        log.info(f"Searching for transactions relating to bot message {message_id}")
        bot_message_record = await self.find_bot_message_by_message_id(message_id)
        if bot_message_record is None:
            log.info("No matching records found")
            return None
        else:
            bot_message = BotMessage.from_airtable(bot_message_record)
            transaction_record = await self._retrieve_transaction(
                bot_message.transaction_id
            )
            return Transaction.from_airtable(transaction_record) or None

    async def delete_bot_message(self, record_id: str, session: ClientSession = None):
        """Delete the specified bot_message record."""
        records_to_delete = [record_id]
        log.info(f"Deleting records {records_to_delete}")
        await self._delete(self.bot_messages_url, records_to_delete, session)
