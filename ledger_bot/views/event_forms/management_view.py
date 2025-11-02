"""Main event management views and buttons."""

import logging
from typing import TYPE_CHECKING, Any

import discord

from ledger_bot.message_generators import generate_event_detail_message
from ledger_bot.models import Event, Member

from .basic_fields import (
    SetDescriptionButton,
    SetLocationButton,
    SetNameButton,
)
from .date_fields import (
    SetDateButton,
    SetOngoingButton,
    SetTBDButton,
)
from .financial_fields import (
    SetDepositValueButton,
    SetMaxGuestsButton,
)
from .member_management import (
    AddHostButton,
    AddMemberButton,
)

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class ToggleIsPrivateButton(discord.ui.Button):
    """Button to toggle event privacy status."""

    event: Event

    def _label(self):
        return "Make Event Public" if self.event.is_private else "Make Event Private"

    def _style(self):
        return (
            discord.ButtonStyle.success
            if not self.event.is_private
            else discord.ButtonStyle.red
        )

    async def callback(self, interaction: discord.Interaction):
        self.event.is_private = not self.event.is_private

        self.event = await self.client.service.event.update_event(
            self.event, ["is_private"]
        )

        self.label = self._label()
        self.style = self._style()

        await interaction.response.edit_message(view=self.view)

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__(
            label=self._label(),
            style=self._style(),
            custom_id="ToggleIsPrivateButton",
        )


class CreateEventManagementButtons(discord.ui.LayoutView):
    """Main event management interface with all editing options."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
        feedback: str | None = None,
        description: str | None = None,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.feedback = feedback
        self.description = description
        self.event = event

        super().__init__()

        feedback_container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay(self.feedback or "")
        )

        description_container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay(self.description or "")
        )

        event_management_container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay("## Event Management")
        )

        set_details_row: discord.ui.ActionRow = discord.ui.ActionRow()
        set_date_row: discord.ui.ActionRow = discord.ui.ActionRow()
        set_members_row: discord.ui.ActionRow = discord.ui.ActionRow()
        set_status_row: discord.ui.ActionRow = discord.ui.ActionRow()

        set_name_button = SetNameButton(client=client, requestor=requestor, event=event)

        set_description_button = SetDescriptionButton(
            client=client, requestor=requestor, event=event
        )

        set_location_button = SetLocationButton(
            client=client, requestor=requestor, event=event
        )

        set_date_button = SetDateButton(client=client, requestor=requestor, event=event)

        set_ongoing_button = SetOngoingButton(
            client=client, requestor=requestor, event=event
        )

        set_tbd_button = SetTBDButton(client=client, requestor=requestor, event=event)

        set_max_guests_button = SetMaxGuestsButton(
            client=client, requestor=requestor, event=event
        )

        set_deposit_value_button = SetDepositValueButton(
            client=client, requestor=requestor, event=event
        )

        add_member_button = AddMemberButton(
            client=client, requestor=requestor, event=event
        )

        add_host_button = AddHostButton(client=client, requestor=requestor, event=event)

        toggle_is_private_button = ToggleIsPrivateButton(
            client=client, requestor=requestor, event=event
        )

        # Add buttons to row
        set_details_row.add_item(set_name_button)
        set_details_row.add_item(set_description_button)
        set_details_row.add_item(set_location_button)
        set_details_row.add_item(set_deposit_value_button)

        set_date_row.add_item(set_date_button)
        set_date_row.add_item(set_ongoing_button)
        set_date_row.add_item(set_tbd_button)

        set_members_row.add_item(set_max_guests_button)

        set_members_row.add_item(add_member_button)
        set_members_row.add_item(add_host_button)

        set_status_row.add_item(toggle_is_private_button)

        # Add rows to containers
        event_management_container.add_item(set_details_row)
        event_management_container.add_item(set_date_row)
        event_management_container.add_item(set_members_row)
        event_management_container.add_item(set_status_row)

        # Add containers to self
        if self.feedback:
            self.add_item(feedback_container)

        self.add_item(description_container)
        self.add_item(event_management_container)


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

            # Get all hosts for this event
            event_hosts = await self.client.service.event_member.get_hosts_for_event(
                event_id=self.event.id,
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

            # User is a valid host, show the management buttons
            management_view = CreateEventManagementButtons(
                client=self.client,
                requestor=member,
                event=self.event,
                feedback=None,
                description=await generate_event_detail_message(
                    self.event, self.client
                ),
            )

            await interaction.followup.send(
                view=management_view,
                ephemeral=True,
            )
