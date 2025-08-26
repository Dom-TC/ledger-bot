"""Register our slash commands with Discord."""

import logging
from typing import TYPE_CHECKING, Any, Dict

import discord
from discord import app_commands

from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.services import Service

from .command_add_role import command_add_role
from .command_hello import command_hello
from .command_help import command_help
from .command_list import command_list
from .command_new_sale import command_new_sale
from .command_new_split import command_new_split
from .command_stats import command_stats

log = logging.getLogger(__name__)


def setup_slash(
    client: LedgerBot,
) -> None:
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
    async def hello(interaction: discord.Interaction[Any]) -> None:
        """Says hello."""
        await command_hello(
            client=client,
            interaction=interaction,
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
        interaction: discord.Interaction[Any],
        wine_name: str,
        buyer: discord.Member,
        price: float,
    ) -> None:
        await command_new_sale(
            client=client,
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
        interaction: discord.Interaction[Any],
        wine_name: str,
        price: float,
        buyer_1: discord.Member,
        buyer_2: discord.Member,
        buyer_3: discord.Member,
        buyer_4: discord.Member,
        buyer_5: discord.Member,
        buyer_6: discord.Member,
    ) -> None:
        log.info(f"Recognised command: /new_split from {interaction.user.name}")
        buyers = [buyer_1, buyer_2, buyer_3, buyer_4, buyer_5, buyer_6]
        await command_new_split(
            client=client,
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
        interaction: discord.Interaction[Any],
        wine_name: str,
        price: float,
        buyer_1: discord.Member,
        buyer_2: discord.Member,
        buyer_3: discord.Member,
    ) -> None:
        log.info(f"Recognised command: /new_split_3 from {interaction.user.name}")
        buyers = [buyer_1, buyer_2, buyer_3]
        await command_new_split(
            client=client,
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
        interaction: discord.Interaction[Any],
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
    ) -> None:
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
            interaction=interaction,
            wine_name=wine_name,
            buyers=buyers,
            price=price,
        )

    @client.tree.command(
        guild=client.guild, name="help", description="Get help information"
    )
    async def slash_help(interaction: discord.Interaction[Any]) -> None:
        """Gets help information."""
        await command_help(
            client=client,
            interaction=interaction,
        )

    @client.tree.command(
        guild=client.guild, name="list", description="List your transactions"
    )
    async def slash_list(interaction: discord.Interaction[Any]) -> None:
        """Returns a list of the users transactions."""
        log.info(f"Recognised command: /list from {interaction.user.name}")
        await command_list(
            client=client,
            interaction=interaction,
        )

    @client.tree.command(
        guild=client.guild, name="stats", description="View your stats"
    )
    async def stats(interaction: discord.Interaction[Any]) -> None:
        """Returns a list of the users transactions."""
        log.info(f"Recognised command: /stats from {interaction.user.name}")
        await command_stats(
            client=client,
            interaction=interaction,
        )

    async def check_is_admin_or_maintainer(interaction: discord.Interaction) -> bool:
        log.debug(
            f"Checking if user {interaction.user.name} is either an admin or a maintainer"
        )
        return await client.is_admin_or_maintainer(user_id=interaction.user.id)

    @client.tree.command(
        guild=client.guild,
        name="add_role",
        description="Admin: add a role to the reactions database.",
    )
    @app_commands.check(check_is_admin_or_maintainer)
    @app_commands.describe(
        role="The role to add to the database",
        emoji="The emoji for the reaction",
        message_id="The message to monitor for reactions.",
    )
    async def add_role(
        interaction: discord.Interaction[Any],
        role: discord.Role,
        emoji: str,
        message_id: str,
    ) -> None:
        """Add a role to the reactions database."""
        log.info(f"Recognised command: /add_role from {interaction.user.name}")
        await command_add_role(
            client=client,
            interaction=interaction,
            role=role,
            emoji=emoji,
            message_id=int(message_id),
        )

    @add_role.error
    async def add_role_error(interaction: discord.Interaction[Any], error: Exception):
        if isinstance(error, discord.app_commands.CheckFailure):
            log.error(
                f"User {interaction.user.name} doesn't have permission to add a role."
            )
            await interaction.response.send_message(
                "You don't have permission to add a role.", ephemeral=True
            )
        else:
            log.error("An unhandled error occured", exc_info=error)
