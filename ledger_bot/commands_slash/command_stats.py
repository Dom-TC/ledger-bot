"""Slash command - stats."""

import logging
from typing import TYPE_CHECKING, Any

import discord

from ledger_bot.message_generators import generate_stats_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_stats(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
) -> None:
    """DM command - stats."""
    log.info(f"Getting stats for user {interaction.user.name} ({interaction.user.id})")

    # Defer interaction so we can respond to it later
    await interaction.response.defer(ephemeral=True)

    stats_obj = await client.service.stats.get_stats(
        user=await client.service.member.get_or_add_member(interaction.user)
    )

    if stats_obj.server is None:
        await interaction.response.send_message("No transactions have been recorded.")

    else:
        response = generate_stats_message(stats=stats_obj)

        await interaction.followup.send(response, ephemeral=True)
