"""DM command - list."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.message_generators import generate_list_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_list(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - list."""
    log.info(f"Getting transactions for user {message.author.name}")

    try:
        async with client.session_factory() as session:
            member = await client.service.member.get_or_add_member(
                message.author, session=session
            )

            await session.refresh(
                member, attribute_names=["buying_transactions", "selling_transactions"]
            )

            buy_transactions = member.buying_transactions
            sell_transactions = member.selling_transactions

            transactions = buy_transactions + sell_transactions

            # Load bot_messages for each transaction
            for tx in transactions:
                await session.refresh(
                    tx, attribute_names=["seller", "buyer", "bot_messages"]
                )

    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await dm_channel.send("An unexpected error occured.")
        return

    if transactions is None:
        await dm_channel.send("You don't have any transactions.")
    else:
        response = await generate_list_message(
            transactions=transactions,
            user_id=message.author.id,
            service=client.service,
        )

        for transmit_message in response:
            await dm_channel.send(transmit_message)
