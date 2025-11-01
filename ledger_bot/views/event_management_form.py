"""Views and Modals for hosts interacting with events."""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import discord

from ledger_bot.models import Event, EventMemberStatus, Member
from ledger_bot.utils import build_datetime, is_valid_timezone

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class CreateEventManagementButtons(discord.ui.LayoutView):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        feedback: str | None = None,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.feedback = feedback

        super().__init__()

        feedback_container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay(self.feedback or "")
        )

        user_settings_container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay("# Event Management")
        )

        user_settings_row: discord.ui.ActionRow = discord.ui.ActionRow()

        # Add rows to containers
        user_settings_container.add_item(user_settings_row)

        # Add containers to self
        if self.feedback:
            self.add_item(feedback_container)

        self.add_item(user_settings_container)


class ManageEventButton(discord.ui.View):
    """A simple view with a 'Manage Event' button that shows management options to hosts."""

    def __init__(
        self,
        client: "LedgerBot",
        event: Event,
    ) -> None:
        self.client = client
        self.event = event
        super().__init__(timeout=None)  # Persistent view, no timeout

    @discord.ui.button(label="Manage Event", style=discord.ButtonStyle.primary)
    async def manage_event_button(
        self, interaction: discord.Interaction[Any], _button: discord.ui.Button[Any]
    ) -> None:
        """Handle the manage event button click."""
        # Defer the response as ephemeral immediately
        await interaction.response.defer(ephemeral=True)

        # Check if the user is a discord.Member
        if not isinstance(interaction.user, discord.Member):
            log.error(
                f"interaction.user isn't a discord.Member. {interaction.user} / {type(interaction.user)}"
            )
            await interaction.followup.send(
                content="An unexpected error occurred. Please try again later.",
                ephemeral=True,
            )
            return

        # Get or add the member
        async with self.client.session_factory() as session:
            member = await self.client.service.member.get_or_add_member(
                interaction.user, session=session
            )

            # Get all event members for this event
            event_members = (
                await self.client.service.event_member.list_event_members_by_event(
                    event_id=self.event.id,
                    session=session,
                )
            )

            # Find this specific member in the event members list
            user_event_member = next(
                (em for em in event_members if em.member_id == member.id), None
            )

            # Verify user is a host
            if (
                user_event_member is None
                or user_event_member.status != EventMemberStatus.HOST
            ):
                await interaction.followup.send(
                    content="Only event hosts can manage this event.",
                    ephemeral=True,
                )
                return

            # User is a valid host, show the management buttons
            management_view = CreateEventManagementButtons(
                client=self.client,
                requestor=member,
                feedback=None,
            )

            await interaction.followup.send(
                view=management_view,
                ephemeral=True,
            )
