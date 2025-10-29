"""DM command - list."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.core import register_help_command
from ledger_bot.message_generators import generate_list_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


@register_help_command(
    command="list", description="Returns a list of your transactions.", scope="dm"
)
async def command_list(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - list."""
    log.info(f"Getting transactions for user {message.author.name}")

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
