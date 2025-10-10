"""Slash command - lookup."""

import logging
from typing import TYPE_CHECKING, Any

import discord

from ledger_bot.views import CreateSettingsButtons

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_settings(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
) -> None:
    """Lets a user manage their settings."""
    log.info(
        f"Display settings buttons for {interaction.user.name} ({interaction.user.id})"
    )

    # Discord Interactions need to be responded to in <3s or they time out.
    # Depending on the number of transactions a user has, we could take longer, so defer the interaction.
    await interaction.response.defer(ephemeral=True)

    if not interaction.guild:
        log.error("Interaction had no guild")
        await interaction.followup.send(
            "An error occured. Please try again later", ephemeral=True
        )
        return

    requestor = await client.service.member.get_or_add_member(interaction.user)

    await interaction.followup.send(
        view=CreateSettingsButtons(client=client, requestor=requestor), ephemeral=True
    )
