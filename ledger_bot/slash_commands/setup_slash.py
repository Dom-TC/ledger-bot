"""Register our slash commands with Discord."""

import logging

import discord
from discord import app_commands

from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.storage import AirtableStorage

from .command_add_user import command_add_user
from .command_hello import command_hello
from .command_help import command_help
from .command_list import command_list
from .command_new_sale import command_new_sale
from .command_new_split import command_new_split

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
        await command_hello(
            client=client, config=config, storage=storage, interaction=interaction
        )

    @client.tree.command(
        guild=client.guild, name="new_sale", description="Create a new transaction"
    )
    @app_commands.describe(
        wine_name="The wine you're selling.",
        buyer="The name of the user you're selling to.",
        price="The price of the wine",
    )
    async def new_sale(
        interaction: discord.Interaction,
        wine_name: str,
        buyer: discord.Member,
        price: float,
    ):
        await command_new_sale(
            client=client,
            config=config,
            storage=storage,
            interaction=interaction,
            wine_name=wine_name,
            buyer=buyer,
            price=price,
        )

    @client.tree.command(
        guild=client.guild,
        name="new_split",
        description="Split a wine between six people",
    )
    @app_commands.describe(
        wine_name="The wine you're selling.",
        price="The price of the wine",
        buyer_1="The name of the the first person you're selling to.",
        buyer_2="The name of the the second person you're selling to.",
        buyer_3="The name of the the third person you're selling to.",
        buyer_4="The name of the the fourth person you're selling to.",
        buyer_5="The name of the the fifth person you're selling to.",
        buyer_6="The name of the the sixth person you're selling to.",
    )
    async def new_split(
        interaction: discord.Interaction,
        wine_name: str,
        price: float,
        buyer_1: discord.Member,
        buyer_2: discord.Member,
        buyer_3: discord.Member,
        buyer_4: discord.Member,
        buyer_5: discord.Member,
        buyer_6: discord.Member,
    ):
        buyers = [buyer_1, buyer_2, buyer_3, buyer_4, buyer_5, buyer_6]
        await command_new_split(
            client=client,
            config=config,
            storage=storage,
            interaction=interaction,
            wine_name=wine_name,
            buyers=buyers,
            price=price,
        )

    @client.tree.command(
        guild=client.guild, name="help", description="Get help information"
    )
    async def slash_help(interaction: discord.Interaction):
        """Gets help information."""
        await command_help(
            client=client, config=config, storage=storage, interaction=interaction
        )

    @client.tree.command(
        guild=client.guild, name="list", description="List your transactions"
    )
    async def slash_list(interaction: discord.Interaction):
        """Returns a list of the users transactions."""
        log.info(f"Recognised command: /list from {interaction.user.name}")
        await command_list(
            client=client, config=config, storage=storage, interaction=interaction
        )
