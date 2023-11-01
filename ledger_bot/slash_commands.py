"""Ledger Bot's Slash Commands."""

import datetime
import logging

import discord
from discord import app_commands
from LedgerBot import LedgerBot
from models import Transaction
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

    @client.tree.command(
        guild=client.guild, name="list", description="List a transaction"
    )
    @app_commands.describe(
        wine_name="The wine you're selling.",
        buyer="The name of the user you're selling to.",
        price="The price of the wine",
    )
    async def list_transaction(
        interaction: discord.Interaction,
        wine_name: str,
        buyer: discord.Member,
        price: float,
    ):
        """Add transaction to Airtable."""
        log.info("Processing new sale...")
        log.info(f"Getting / adding seller: {interaction.user}")
        seller_record = await storage.get_or_add_member(interaction.user)
        log.info(f"Getting / adding buyer: {buyer}")
        buyer_record = await storage.get_or_add_member(buyer)

        # Build Transaction object from provided data
        transaction = Transaction(
            seller_id=seller_record,
            buyer_id=buyer_record,
            wine=wine_name,
            price=price,
            sale_approved=False,
            delivered=False,
            paid=False,
            cancelled=False,
            creation_date=datetime.datetime.utcnow().isoformat(),
        )

        transaction_fields = [
            "seller_id",
            "buyer_id",
            "wine",
            "price",
            "sale_approved",
            "delivered",
            "paid",
            "cancelled",
            "creation_date",
        ]

        transaction_response = await storage.save_transaction(
            transaction=transaction, fields=transaction_fields
        )

        # Convert response in dict form to Transaction object for future use
        transaction_record = Transaction.from_airtable(transaction_response)

        response_contents = f"*New Sale Listed*\n**{interaction.user.mention} sold {wine_name} to {buyer.mention}**\nPrice: £{price}\n\n**Status**\nApproved: No\nPaid: No\nDelivered: No"

        try:
            await interaction.response.send_message(response_contents)

            # We have to call a different command to get the message we just posted
            bot_message = await interaction.original_response()

            # Update record to include the message ID
            transaction_record.bot_message_id = bot_message.id
            transaction_fields = ["bot_message_id"]
            await storage.save_transaction(
                transaction=transaction_record, fields=transaction_fields
            )

            log.debug(bot_message.id)
        except discord.HTTPException as error:
            log.error(f"An error occured sending the message: {error}")
        except discord.ClientException as error:
            log.error(f"Couldn't get response message channel: {error}")
