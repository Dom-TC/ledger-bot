"""Slash command - new_sale."""

import datetime
import logging
from typing import Any

import discord

from ledger_bot.core import register_help_command
from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import Transaction

log = logging.getLogger(__name__)


@register_help_command(
    command="new_event",
    args=["TBC"],
    description="Creates a new event.",
)
async def command_new_event(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
    event_name: str,
    region: int,
    description: str | None = None,
    location: str | None = None,
) -> None:
    """Register a new event."""
    if isinstance(interaction.channel, discord.channel.TextChannel):
        channel_name = interaction.channel.name
    else:
        channel_name = "DM"

    if channel_name not in client.config.channels.include:
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel not in include list"
        )
        await interaction.response.send_message(
            content=f"{client.config.name} is not available in this channel.",
            ephemeral=True,
        )
        return
    elif channel_name in client.config.channels.exclude:
        log.info(
            f"Ignoring slash command from {interaction.user.name} in {channel_name}  - Channel in exclude list"
        )
        await interaction.response.send_message(
            content=f"{client.config.name} is not available in this channel.",
            ephemeral=True,
        )
        return

    if client.user is None:
        log.critical("The client isn't connected")
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

    async with client.session_factory() as session:
        log.info("Processing new event...")

        # Add event to database

        # Create event channel

        # Post event management post in channel

        # Respond to user confirming event created, ask to manage it in channel.

    response_contents = await generate_transaction_status_message(
        transaction=transaction_record,
        client=client,
        config=client.config,
        is_update=False,
    )
    try:
        await interaction.followup.send(response_contents)

        # We have to call a different command to get the message we just posted
        bot_message = await interaction.original_response()

        await client.service.bot_message.save_transaction_bot_message(
            message=bot_message, transaction=transaction_record
        )

    except discord.HTTPException as error:
        log.error(f"An error occured sending the message: {error}")
    except discord.ClientException as error:
        log.error(f"Couldn't get response message channel: {error}")
