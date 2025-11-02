"""Toggle event field forms: toggle private."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_event_detail_message
from ledger_bot.models import Event, Member

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
        # Import here to avoid circular dependency
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        self.event.is_private = not self.event.is_private

        self.event = await self.client.service.event.update_event(
            self.event, ["is_private"]
        )

        self.label = self._label()
        self.style = self._style()

        feedback = (
            "Set event to private" if self.event.is_private else "Set event to public"
        )

        await self.client.update_event_posts(event=self.event)

        await interaction.response.edit_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
                description=await generate_event_detail_message(
                    self.event, self.client
                ),
            ),
        )

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
