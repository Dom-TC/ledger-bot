"""Slash command - list."""

import logging
from typing import TYPE_CHECKING, Any

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.message_generators import generate_list_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_list(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
) -> None:
    """DM command - list."""
    log.info(
        f"Getting transactions for user {interaction.user.name} ({interaction.user.id})"
    )

    # Discord Interactions need to be responded to in <3s or they time out.
    # Depending on the number of transactions a user has, we could take longer, so defer the interaction.
    await interaction.response.defer(ephemeral=True)

    try:
        async with client.session_factory() as session:
            member = await client.service.member.get_or_add_member(
                interaction.user, session=session
            )

            await session.refresh(
                member, attribute_names=["buying_transactions", "selling_transactions"]
            )

            buy_transactions = member.buying_transactions
            sell_transactions = member.selling_transactions

            transactions = buy_transactions + sell_transactions
    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await interaction.response.send_message(
            "An unexpected error occured.", ephemeral=True
        )
        return

    if transactions is None:
        await interaction.response.send_message("You don't have any transactions.")
    else:
        response = await generate_list_message(
            transactions=transactions,
            user_id=member.discord_id,
            service=client.service,
        )

        for transmit_message in response:
            await interaction.followup.send(transmit_message, ephemeral=True)
