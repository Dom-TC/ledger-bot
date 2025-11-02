"""Date-related event field forms: date, ongoing, TBD."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_event_detail_message
from ledger_bot.models import Event, Member
from ledger_bot.utils import build_datetime
from ledger_bot.validators import DateTimeValidator

from .base import BaseEventFieldButton, BaseEventFieldModal

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class SetDateButton(BaseEventFieldButton):
    """Button to set specific event date."""

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
            label="Update Event Date" if event.event_date else "Set Event Date",
            custom_id="SetDateButton",
            style=(
                discord.ButtonStyle.success
                if event.event_date
                else discord.ButtonStyle.secondary
            ),
        )

    def get_modal_class(self):
        return SetDateModal


class SetDateModal(BaseEventFieldModal):
    """Modal to set specific event date."""

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
            title="Set specific event date",
        )

        log.debug(f"Current date: {event.event_date}, is_ongoing: {event.is_ongoing}")

        # Date input field
        date_placeholder = ""
        if event.event_date:
            date_placeholder = event.event_date.strftime("%d-%m-%Y")

        self.date_input: discord.ui.Label = discord.ui.Label(
            text="Event Date (DD-MM-YYYY)",
            description="Enter the event date",
            component=discord.ui.TextInput(
                placeholder=date_placeholder or "15-01-2025",
                required=True,
            ),
        )

        # Time input field
        time_placeholder = ""
        if event.event_date:
            time_placeholder = event.event_date.strftime("%H:%M")

        self.time_input: discord.ui.Label = discord.ui.Label(
            text="Event Time (HH:MM)",
            description="Enter the event time",
            component=discord.ui.TextInput(
                placeholder=time_placeholder or "18:00",
                required=False,
            ),
        )

        self.add_item(self.date_input)
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        # Fetch the latest event from the database to avoid stale data
        async with self.client.session_factory() as session:
            if not self.event:
                log.warning("Event wasn't provided.")
                return

            event_record = await self.client.service.event.get_event(
                record_id=self.event.id, session=session
            )

            if event_record:
                self.event = event_record

        if self.event is None:
            await interaction.response.send_message(
                "**Failed to update event date.**\nEvent not found.",
            )
            return

        assert isinstance(self.date_input.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.time_input.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        date_str = self.date_input.component.value.strip()
        time_str = self.time_input.component.value.strip()
        timezone_str = "UTC"

        # Validate using the datetime validator
        validator = DateTimeValidator(
            parser=build_datetime, allow_past=True, allow_future=True
        )
        result = validator.validate(
            (date_str, time_str if time_str else "00:00", timezone_str)
        )

        if not result.is_valid:
            feedback = (
                f"**Failed to update event date.**\n"
                f"{result.error_message}\n"
                f"Please use DD-MM-YYYY for date and HH:MM for time."
            )
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
            return

        event_datetime = result.value

        log.info(
            f"Setting event date to {event_datetime} for event {self.event.event_name} ({self.event.id})"
        )

        if not event_datetime:
            feedback = "**Failed to set event date**\nPlease try again later"
            await self.update_and_respond(
                interaction=interaction,
                fields=["event_date", "is_ongoing"],
                feedback=feedback,
                update_channel=True,
            )
            return

        self.event.event_date = event_datetime
        self.event.is_ongoing = False

        feedback = f"**Successfully set event date to {event_datetime.strftime('%Y-%m-%d %H:%M %Z')}.**"

        await self.update_and_respond(
            interaction=interaction,
            fields=["event_date", "is_ongoing"],
            feedback=feedback,
            update_channel=True,
        )


class SetOngoingButton(discord.ui.Button):
    """Button to set event as ongoing."""

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
            label=(
                "Event is Ongoing" if event.is_ongoing else "Set Event Date to Ongoing"
            ),
            style=(
                discord.ButtonStyle.success
                if event.is_ongoing
                else discord.ButtonStyle.secondary
            ),
            custom_id="SetOngoingButton",
        )

    async def callback(self, interaction: discord.Interaction):
        from ledger_bot.errors import EventChannelError
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        # Fetch the latest event from the database to avoid stale data
        if not self.event:
            return

        async with self.client.session_factory() as session:

            event_record = await self.client.service.event.get_event(
                record_id=self.event.id, session=session
            )

            if event_record:
                self.event = event_record

        if self.event is None:
            await interaction.response.send_message(
                "**Failed to set event as ongoing.**\nEvent not found.",
            )
            return

        # Store old values for rollback if needed
        old_event_date = self.event.event_date
        old_is_ongoing = self.event.is_ongoing

        log.info(
            f"Setting event as ongoing for event {self.event.event_name} ({self.event.id})"
        )

        self.event.event_date = None
        self.event.is_ongoing = True

        # Update the event in the database
        self.event = await self.client.service.event.update_event(
            event=self.event,
            fields=["event_date", "is_ongoing"],
        )

        # Try to update the channel name
        try:
            await self.client.update_channel_name(event=self.event)

        except EventChannelError:
            log.error("Failed to update event channel name")

            # Rollback the changes
            self.event.event_date = old_event_date
            self.event.is_ongoing = old_is_ongoing
            self.event = await self.client.service.event.update_event(
                event=self.event,
                fields=["event_date", "is_ongoing"],
            )

            feedback = (
                "**Failed to set event as ongoing.**\nAn unexpected error occurred."
            )

        else:
            feedback = "**Successfully set event as ongoing.**"

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


class SetTBDButton(discord.ui.Button):
    """Button to set event date as TBD (To Be Determined)."""

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
            label=(
                "Date is TBD"
                if not event.is_ongoing and not event.event_date
                else "Set Event Date to TBD"
            ),
            style=(
                discord.ButtonStyle.success
                if not event.is_ongoing and not event.event_date
                else discord.ButtonStyle.secondary
            ),
            custom_id="SetTBDButton",
        )

    async def callback(self, interaction: discord.Interaction):
        from ledger_bot.errors import EventChannelError
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        # Fetch the latest event from the database to avoid stale data
        if not self.event:
            return

        async with self.client.session_factory() as session:
            event_record = await self.client.service.event.get_event(
                record_id=self.event.id, session=session
            )

            if event_record:
                self.event = event_record

        if self.event is None:
            await interaction.response.send_message(
                "**Failed to set event as TBD.**\nEvent not found.",
            )
            return

        # Store old values for rollback if needed
        old_event_date = self.event.event_date
        old_is_ongoing = self.event.is_ongoing

        log.info(
            f"Clearing date and ongoing for event {self.event.event_name} ({self.event.id})"
        )

        self.event.event_date = None
        self.event.is_ongoing = False

        # Update the event in the database
        self.event = await self.client.service.event.update_event(
            event=self.event,
            fields=["event_date", "is_ongoing"],
        )

        # Try to update the channel name
        try:
            await self.client.update_channel_name(event=self.event)

        except EventChannelError:
            log.error("Failed to update event channel name")

            # Rollback the changes
            self.event.event_date = old_event_date
            self.event.is_ongoing = old_is_ongoing
            self.event = await self.client.service.event.update_event(
                event=self.event,
                fields=["event_date", "is_ongoing"],
            )

            feedback = "**Failed to set event as TBD.**\nAn unexpected error occurred."

        else:
            feedback = "**Successfully set event as TBD.**"

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
