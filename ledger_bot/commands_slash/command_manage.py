"""Slash command - manage."""

import logging
from typing import Any

import discord

from ledger_bot import views
from ledger_bot.core import register_help_command
from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


@register_help_command(
    command="manage",
    args=[],
    description="Manage the event in the current channel.",
)
async def command_manage(
    client: "LedgerBot",
    interaction: discord.Interaction[Any],
) -> None:
    """Manage an event if the user is in a valid event channel and is a host."""
    # Check if the user is a discord.Member
    if not isinstance(interaction.user, discord.Member):
        log.error(
            f"interaction.user isn't a discord.Member. {interaction.user} / {type(interaction.user)}"
        )
        await interaction.response.send_message(
            content="An unexpected error occurred. Please try again later.",
            ephemeral=True,
        )
        return

    # Check if the command is being used in a text channel
    if not isinstance(interaction.channel, discord.TextChannel):
        log.info(
            f"Ignoring /manage from {interaction.user.name} - not in a text channel"
        )
        await interaction.response.send_message(
            content="This command can only be used in event channels.",
            ephemeral=True,
        )
        return

    # Defer the response as ephemeral immediately
    await interaction.response.defer(ephemeral=True)

    async with client.session_factory() as session:
        # Get the event associated with this channel
        event = await client.service.event.get_event_by_channel_id(
            channel_id=interaction.channel.id,
            session=session,
        )

        if event is None:
            log.info(
                f"No event found for channel {interaction.channel.name} (ID: {interaction.channel.id})"
            )
            await interaction.followup.send(
                content="This channel is not associated with an event.",
                ephemeral=True,
            )
            return

        # Get or add the member
        member = await client.service.member.get_or_add_member(
            interaction.user, session=session
        )

        # Get all hosts for this event
        event_hosts = await client.service.event_member.get_hosts_for_event(
            event_id=event.id,
            session=session,
        )

        # Check if the user is a host
        user_is_host = any(host.member_id == member.id for host in event_hosts)

        # Verify user is a host
        if not user_is_host:
            await interaction.followup.send(
                content="Only event hosts can manage this event.",
                ephemeral=True,
            )
            return

        # User is a valid host in a valid event channel, show the management buttons
        management_view = views.CreateEventManagementButtons(
            client=client,
            requestor=member,
            feedback=None,
        )

        await interaction.followup.send(
            view=management_view,
            ephemeral=True,
        )
