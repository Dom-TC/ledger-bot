"""Base classes for event management forms."""

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import discord

from ledger_bot.errors import EventChannelError
from ledger_bot.message_generators import generate_event_detail_message
from ledger_bot.models import Event, Member

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot
    from ledger_bot.validators import ValidationResult, Validator

log = logging.getLogger(__name__)


class BaseEventFieldButton(discord.ui.Button):
    """Base button that opens a modal to edit an event field."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
        label: str,
        custom_id: str,
        style: discord.ButtonStyle = discord.ButtonStyle.primary,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event
        super().__init__(
            label=label,
            style=style,
            custom_id=custom_id,
        )

    def get_modal_class(self):
        """Override in subclass to return the modal class."""
        raise NotImplementedError

    async def callback(self, interaction: discord.Interaction):
        """Open the modal for this field."""
        modal = self.get_modal_class()(
            client=self.client,
            requestor=self.requestor,
            event=self.event,
        )
        await interaction.response.send_modal(modal)


class BaseEventFieldModal(discord.ui.Modal):
    """Base modal for updating event fields with common error handling."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
        title: str,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event
        super().__init__(title=title)

    async def update_and_respond(
        self,
        interaction: discord.Interaction,
        fields: List[str],
        feedback: str,
        update_channel: bool = False,
    ) -> None:
        """Update event fields and send response with common error handling.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction to respond to
        fields : List[str]
            List of field names that were updated
        feedback : str
            Success feedback message to display
        update_channel : bool, optional
            Whether to update the event channel name, by default False
        """
        # Import here to avoid circular dependency
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        # Store old values for rollback if needed
        old_values = {field: getattr(self.event, field) for field in fields}

        # Update the event in the database
        self.event = await self.client.service.event.update_event(
            event=self.event,
            fields=fields,
        )

        # Try to update the channel name if requested
        if update_channel:
            try:
                await self.client.update_channel_name(event=self.event)

            except EventChannelError:
                log.error("Failed to update event channel name")

                # Rollback the changes
                for field, value in old_values.items():
                    setattr(self.event, field, value)
                self.event = await self.client.service.event.update_event(
                    event=self.event,
                    fields=fields,
                )

                feedback = "**Failed to update.**\nAn unexpected error occurred."

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

    async def validate_and_respond(
        self,
        interaction: discord.Interaction,
        value: Any,
        validator: "Validator",
        on_success: Callable[["ValidationResult"], None],
        field_name: str = "field",
    ) -> bool:
        """Validate input and respond with error if validation fails.

        This is a helper method that encapsulates the common pattern of:
        1. Validating input
        2. Sending error message if validation fails
        3. Calling success callback if validation passes

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction to respond to
        value : Any
            The value to validate
        validator : Validator
            The validator to use
        on_success : Callable[[ValidationResult], None]
            Callback to execute on successful validation, receives the ValidationResult
        field_name : str, optional
            Name of the field being validated (for error messages), by default "field"

        Returns
        -------
        bool
            True if validation passed, False otherwise
        """
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        result = validator.validate(value)

        if not result.is_valid:
            feedback = f"**Failed to update {field_name}.**\n{result.error_message}"

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
            return False

        # Validation passed, call success callback
        on_success(result)
        return True
