"""Slash command - new_split."""

import datetime
import logging
from typing import Any, Dict, List

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import Transaction
from ledger_bot.process_transactions import send_message
from ledger_bot.storage_airtable import AirtableStorage

log = logging.getLogger(__name__)


async def command_new_split(
    client: "LedgerBot",
    config: Dict[str, Any],
    storage: AirtableStorage,
    interaction: discord.Interaction[Any],
    wine_name: str,
    buyers: List[discord.Member],
    price: float,
) -> None:
    """Add transaction to Airtable."""
    log.debug(f"Processing command {interaction.command}")

    if isinstance(interaction.channel, discord.channel.TextChannel):
        channel_name = interaction.channel.name
    else:
        channel_name = "DM"

    if (
        config["channels"].get("include")
        and channel_name not in config["channels"]["include"]
    ):
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel not in include list"
        )
        await interaction.response.send_message(
            content=f"{config['name']} is not available in this channel.",
            ephemeral=True,
        )
        return
    elif channel_name in config["channels"].get("exclude", []):
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel in exclude list"
        )
        await interaction.response.send_message(
            content=f"{config['name']} is not available in this channel.",
            ephemeral=True,
        )
        return

    if client.user is None:
        log.critical("The client isn't connected")
        return

    # If user isn't a maintainer, they shouldn't be able to sell to either ledger-bot.
    if interaction.user.id not in client.config["maintainer_ids"]:
        for buyer in buyers:
            if buyer.id == client.user.id:
                log.info(f"Rejecting sale to ledger-bot from {interaction.user.name}")
                await interaction.response.send_message(
                    content=f"You can't sell a wine to {config['name']}!",
                    ephemeral=True,
                )
                return

    # Discord Interactions need to be responded to in <3s or they time out.  We take longer, so defer the interaction.
    # We can't dynamically choose whether the response will be ephemeral or not, so this has to be after the above channel checks, or they can't be emphemeral.
    await interaction.response.defer()

    log.info("Processing split...")

    count = 0
    for buyer in buyers:
        log.info("Processing new sale...")

        if buyer.id == interaction.user.id:
            log.info("Ignoring sale to self")
            await interaction.followup.send(
                "You've kept a bottle for yourself. No transaction created.",
                ephemeral=True,
            )
            continue

        if not isinstance(interaction.user, discord.Member):
            log.error(
                f"interaction.user isn't a discord.Member. {interaction.user} / {type(interaction.user)}"
            )
            await interaction.response.send_message(
                content="An unexpected error occured. Please try again later.",
                ephemeral=True,
            )
            return

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
            buyer_marked_delivered=False,
            seller_marked_delivered=False,
            buyer_marked_paid=False,
            seller_marked_paid=False,
            cancelled=False,
            creation_date=datetime.datetime.utcnow().isoformat(),
        )

        # Format price to 2dp
        price = float("{:.2f}".format(price))
        log.debug(f"{price=}, {type(price)}")

        transaction_fields = [
            "seller_id",
            "buyer_id",
            "wine",
            "price",
            "sale_approved",
            "buyer_marked_delivered",
            "seller_marked_delivered",
            "buyer_marked_paid",
            "seller_marked_paid",
            "cancelled",
            "creation_date",
        ]

        transaction_record = await storage.save_transaction(
            transaction=transaction, fields=transaction_fields
        )

        response_contents = generate_transaction_status_message(
            seller=interaction.user,
            buyer=buyer,
            wine_name=wine_name,
            wine_price=price,
            config=config,
            transaction_id=transaction_record.row_id,
        )
        await send_message(
            response_contents=response_contents,
            channel=interaction.channel,
            target_transaction=transaction_record,
            previous_message_id=None,
            storage=storage,
            config=config,
        )

        count += 1

    await interaction.followup.send(
        f"{count} transactions have been created from your split.",
        ephemeral=True,
    )
