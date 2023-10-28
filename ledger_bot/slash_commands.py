"""Ledger Bot's Slash Commands."""

import logging

import discord
from LedgerBot import LedgerBot
from storage import AirtableStorage

log = logging.getLogger(__name__)


def setup_slash(client: LedgerBot, config: dict, storage: AirtableStorage):
    """
    Builds the available slash commands.

    Paramaters
    ----------
    client : LedgerBot
        The client which is building the commands

    config : dict
        The configuration settings

    storage : AirtableStorage
        The Airtable storage
    """
    client.tree.clear_commands(guild=None)
    client.tree.clear_commands(guild=client.guild)

    @client.tree.command(guild=client.guild)
    async def hello(interaction: discord.Interaction):
        """Says hello."""
        await interaction.response.send_message(f"Hi, {interaction.user.mention}")

    @client.tree.command(guild=client.guild)
    async def add_user(interaction: discord.Interaction):
        """Add user to Airtable."""
        log.info(f"Adding member: {interaction.user}")
        await storage.get_or_add_member(interaction.user)
        await interaction.response.send_message(
            f"You've been added to the database, {interaction.user.mention}"
        )
