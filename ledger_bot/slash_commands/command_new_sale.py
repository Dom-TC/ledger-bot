"""Slash command - new_sale."""

import datetime
import logging
from typing import Any, Dict

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

log = logging.getLogger(__name__)


async def command_new_sale(
    client: "LedgerBot",
    config: Dict[str, Any],
    storage: AirtableStorage,
    interaction: discord.Interaction[Any],
    wine_name: str,
    buyer: discord.Member,
    price: float,
) -> None:
    """Add transaction to Airtable."""
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

    # If user isn't a maintainer, they shouldn't be able to sell to either ledger-bot, or themselves.
    if interaction.user.id not in client.config["maintainer_ids"]:
        if buyer.id == interaction.user.id:
            log.info(f"Rejecting sale to self from {interaction.user.name}")
            await interaction.response.send_message(
                content="You can't sell a wine to yourself!", ephemeral=True
            )
            return

        if buyer.id == client.user.id:
            log.info(f"Rejecting sale to ledger-bot from {interaction.user.name}")
            await interaction.response.send_message(
                content=f"You can't sell a wine to {config['name']}!", ephemeral=True
            )
            return

    # Discord Interactions need to be responded to in <3s or they time out.  We take longer, so defer the interaction.
    # We can't dynamically choose whether the response will be ephemeral or not, so this has to be after the above channel checks, or they can't be emphemeral.
    await interaction.response.defer()

    if not isinstance(interaction.user, discord.Member):
        log.error(
            f"interaction.user isn't a discord.Member. {interaction.user} / {type(interaction.user)}"
        )
        await interaction.followup.send(
            content="An unexpected error occured. Please try again later.",
            ephemeral=True,
        )
        return

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

    transaction_response = await storage.save_transaction(
        transaction=transaction, fields=transaction_fields
    )

    # Convert response in dict form to Transaction object for future use
    transaction_record = Transaction.from_airtable(transaction_response)

    response_contents = generate_transaction_status_message(
        seller=interaction.user,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=price,
        config=config,
    )
    try:
        await interaction.followup.send(response_contents)

        # We have to call a different command to get the message we just posted
        bot_message = await interaction.original_response()

        await storage.record_bot_message(
            message=bot_message, transaction=transaction_record
        )

    except discord.HTTPException as error:
        log.error(f"An error occured sending the message: {error}")
    except discord.ClientException as error:
        log.error(f"Couldn't get response message channel: {error}")
    except AirTableError as error:
        log.error(f"An error occured storing the content in AirTable: {error}")
