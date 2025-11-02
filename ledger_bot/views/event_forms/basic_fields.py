"""Basic event field forms: name, description, location."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.models import Event, Member

from .base import BaseEventFieldButton, BaseEventFieldModal

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class SetNameButton(BaseEventFieldButton):
    """Button to update event name."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        super().__init__(
            client=client,
            requestor=requestor,
            event=event,
            label="Update Event Name",
            custom_id="SetNameButton",
            style=discord.ButtonStyle.primary,
        )

    def get_modal_class(self):
        return SetNameModal


class SetNameModal(BaseEventFieldModal):
    """Modal to set event name."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        super().__init__(
            client=client,
            requestor=requestor,
            event=event,
            title="Set the event name",
        )

        log.debug(f"current name: {event.event_name}")

        self.name_input: discord.ui.Label = discord.ui.Label(
            text="Event Name",
            description="What should the event be called?",
            component=discord.ui.TextInput(
                placeholder=event.event_name,
            ),
        )

        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.name_input.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        new_name = self.name_input.component.value

        log.info(f"Storing event name {new_name} for event {self.event.id}")

        self.event.event_name = new_name

        await self.update_and_respond(
            interaction=interaction,
            fields=["event_name"],
            feedback="**Successfully updated event name.**",
            update_channel=True,
        )


class SetDescriptionButton(BaseEventFieldButton):
    """Button to update event description."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        super().__init__(
            client=client,
            requestor=requestor,
            event=event,
            label=(
                "Update Event Description"
                if event.event_description
                else "Set Event Description"
            ),
            custom_id="SetDescriptionButton",
            style=discord.ButtonStyle.primary,
        )

    def get_modal_class(self):
        return SetDescriptionModal


class SetDescriptionModal(BaseEventFieldModal):
    """Modal to set event description."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        super().__init__(
            client=client,
            requestor=requestor,
            event=event,
            title="Set the event description",
        )

        log.debug(f"current description: {event.event_name}")

        self.description_input: discord.ui.Label = discord.ui.Label(
            text="Event Description",
            description="What's the events description?",
            component=discord.ui.TextInput(
                placeholder=event.event_description,
            ),
        )

        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(
            self.description_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        description = self.description_input.component.value

        log.info(
            f"Storing event description {description} for event {self.event.event_name} ({self.event.id})"
        )

        self.event.event_description = description

        await self.update_and_respond(
            interaction=interaction,
            fields=["event_description"],
            feedback="**Successfully updated event description.**",
        )


class SetLocationButton(BaseEventFieldButton):
    """Button to update event location."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        super().__init__(
            client=client,
            requestor=requestor,
            event=event,
            label=(
                "Update Event Location"
                if event.event_location
                else "Set Event Location"
            ),
            custom_id="SetLocationButton",
            style=discord.ButtonStyle.primary,
        )

    def get_modal_class(self):
        return SetLocationModal


class SetLocationModal(BaseEventFieldModal):
    """Modal to set event location."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        super().__init__(
            client=client,
            requestor=requestor,
            event=event,
            title="Set the event location",
        )

        log.debug(f"Current location: {event.event_name}")

        self.description_input: discord.ui.Label = discord.ui.Label(
            text="Event Location",
            description="What's the events location?",
            component=discord.ui.TextInput(
                placeholder=event.event_location,
            ),
        )

        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(
            self.description_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        location = self.description_input.component.value

        log.info(
            f"Storing event location {location} for event {self.event.event_name} ({self.event.id})"
        )

        self.event.event_location = location

        await self.update_and_respond(
            interaction=interaction,
            fields=["event_location"],
            feedback="**Successfully updated event location.**",
        )
