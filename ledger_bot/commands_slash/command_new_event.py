"""Slash command - new_sale."""

import logging
from typing import Any

import discord

from ledger_bot import views
from ledger_bot.core import register_help_command
from ledger_bot.errors import EventChannelError
from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.models import Event, EventMember, EventMemberStatus

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
) -> None:
    """Register a new event."""
    if isinstance(interaction.channel, discord.channel.TextChannel):
        channel_name = interaction.channel.name
    else:
        channel_name = "DM"

    if channel_name in client.config.channels.exclude:
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

    # Discord Interactions need to be responded to in <3s or they time out.  We might take longer, so defer the interaction.
    # We can't dynamically choose whether the response will be ephemeral or not, so this has to be after the above channel checks, or they can't be emphemeral.
    await interaction.response.defer(ephemeral=True)

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

        log.info("Building base event")
        raw_event = Event(
            event_name=event_name,
            region_id=region,
        )

        # Add event to database
        event = await client.service.event.add_event(raw_event, session=session)

        # Create event channel
        event_channel: discord.TextChannel | None = None
        try:
            event_channel = await client.create_event_channel(
                event=event, session=session
            )

        except EventChannelError:
            log.error("Failed to create channel.")
            await client.service.event.delete_event(event, session=session)
            await interaction.followup.send(
                "Failed to create event channel.  Please try again later. ",
                ephemeral=True,
            )

        if event_channel is None:
            log.debug("Event already has a channel.")
            return

        event.channel_jump_url = event_channel.jump_url

        event = await client.service.event.update_event(event=event, session=session)

        log.info(f"Getting / adding host: {interaction.user}")
        host = await client.service.member.get_or_add_member(
            interaction.user, session=session
        )

        raw_host_em = EventMember(
            event_id=event.id,
            member_id=host.id,
            status=EventMemberStatus.HOST,
            has_paid=1,
        )

        await client.service.event_member.add_event_member(raw_host_em, session=session)

        # Post event management post in channel
        manage_event_view = views.ManageEventButton(
            client=client,
            event=event,
        )

        await event_channel.send(
            content="**Event Management**\nClick the button below to manage this event.\nYou can also use `/manage` at any time.",
            view=manage_event_view,
        )

    # Respond to user confirming event created, ask to manage it in channel.
    try:
        response_contents = f"Successfully created event {event.event_name}.\nTo manage it please go to {event.channel_jump_url}."
        await interaction.followup.send(response_contents)

    except discord.HTTPException as error:
        log.error(f"An error occured sending the message: {error}")
    except discord.ClientException as error:
        log.error(f"Couldn't get response message channel: {error}")
