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
from .command_stats import command_stats

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
        log.info(f"Recognised command: /new_split from {interaction.user.name}")
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
        guild=client.guild,
        name="new_split_3",
        description="Split a wine between three people",
    )
    @app_commands.describe(
        wine_name="The wine you're selling.",
        price="The price of the wine",
        buyer_1="The name of the the first person you're selling to.",
        buyer_2="The name of the the second person you're selling to.",
        buyer_3="The name of the the third person you're selling to.",
    )
    async def new_split_3(
        interaction: discord.Interaction,
        wine_name: str,
        price: float,
        buyer_1: discord.Member,
        buyer_2: discord.Member,
        buyer_3: discord.Member,
    ):
        log.info(f"Recognised command: /new_split_3 from {interaction.user.name}")
        buyers = [buyer_1, buyer_2, buyer_3]
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
        guild=client.guild,
        name="new_split_12",
        description="Split a wine between twelve people",
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
        buyer_7="The name of the the seventh person you're selling to.",
        buyer_8="The name of the the eighth person you're selling to.",
        buyer_9="The name of the the nineth person you're selling to.",
        buyer_10="The name of the the tenth person you're selling to.",
        buyer_11="The name of the the eleventh person you're selling to.",
        buyer_12="The name of the the twelfth person you're selling to.",
    )
    async def new_split_12(
        interaction: discord.Interaction,
        wine_name: str,
        price: float,
        buyer_1: discord.Member,
        buyer_2: discord.Member,
        buyer_3: discord.Member,
        buyer_4: discord.Member,
        buyer_5: discord.Member,
        buyer_6: discord.Member,
        buyer_7: discord.Member,
        buyer_8: discord.Member,
        buyer_9: discord.Member,
        buyer_10: discord.Member,
        buyer_11: discord.Member,
        buyer_12: discord.Member,
    ):
        log.info(f"Recognised command: /new_split_12 from {interaction.user.name}")
        buyers = [
            buyer_1,
            buyer_2,
            buyer_3,
            buyer_4,
            buyer_5,
            buyer_6,
            buyer_7,
            buyer_8,
            buyer_9,
            buyer_10,
            buyer_11,
            buyer_12,
        ]
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

    @client.tree.command(
        guild=client.guild, name="stats", description="View your stats"
    )
    async def stats(interaction: discord.Interaction):
        """Returns a list of the users transactions."""
        log.info(f"Recognised command: /stats from {interaction.user.name}")
        await command_stats(
            client=client, config=config, storage=storage, interaction=interaction
        )
