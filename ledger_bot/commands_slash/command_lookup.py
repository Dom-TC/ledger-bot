"""Slash command - lookup."""

import logging
from typing import TYPE_CHECKING, Any, Dict

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.models import ReactionRole
from ledger_bot.services import Service
from ledger_bot.utils import add_reaction, is_valid_emoji

if TYPE_CHECKING:
    from ledger_bot.clients import ReactionRolesClient

log = logging.getLogger(__name__)


async def command_lookup(
    client: "ReactionRolesClient",
    interaction: discord.Interaction[Any],
    user: discord.Member,
) -> None:
    """Lookup another users transactions."""
    log.info(f"Looking up transactions for {user.name} ({user.id})")

    # Discord Interactions need to be responded to in <3s or they time out.
    # Depending on the number of transactions a user has, we could take longer, so defer the interaction.
    await interaction.response.defer(ephemeral=True)

    try:
        async with client.session_factory() as session:
            member = await client.service.member.get_or_add_member(
                user, session=session
            )

            await session.refresh(
                member, attribute_names=["buying_transactions", "selling_transactions"]
            )

            transaction_summary = (
                await client.service.member.get_member_transaction_summary(member)
            )

    except AirTableError as error:
        log.error(f"There was an error processing the AirTable request: {error}")
        await interaction.response.send_message(
            "An unexpected error occured.", ephemeral=True
        )
        return

    if not (transaction_summary.purchases_count + transaction_summary.sales_count):
        response = f"<@{member.discord_id}> has no recorded transactions."
    else:
        response = f"<@{member.discord_id}> has {transaction_summary.purchases_count} purchases and {transaction_summary.sales_count} sales.\n\nOf their transactions:\n- {transaction_summary.open_count} are open\n- {transaction_summary.completed_count} are completed\n- {transaction_summary.cancelled_count} are cancelled"

    await interaction.followup.send(response, ephemeral=True)
