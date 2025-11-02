"""Financial event field forms: max guests, deposit value."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_event_detail_message
from ledger_bot.models import Event, Member
from ledger_bot.validators import (
    currency_validator,
    positive_integer_validator,
)

from .base import BaseEventFieldButton, BaseEventFieldModal

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class SetMaxGuestsButton(BaseEventFieldButton):
    """Button to update maximum number of guests."""

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
            label="Update Max Guests" if event.max_guests else "Set Max Guests",
            custom_id="SetMaxGuestsButton",
            style=discord.ButtonStyle.primary,
        )

    def get_modal_class(self):
        return SetMaxGuestsModal


class SetMaxGuestsModal(BaseEventFieldModal):
    """Modal to set maximum number of guests."""

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
            title="Set maximum number of guests",
        )

        log.debug(f"current max_guests: {event.max_guests}")

        self.max_guests_input: discord.ui.Label = discord.ui.Label(
            text="Max Guests",
            description="Maximum number of guests allowed",
            component=discord.ui.TextInput(
                placeholder=str(event.max_guests) if event.max_guests else "10",
            ),
        )

        self.add_item(self.max_guests_input)

    async def on_submit(self, interaction: discord.Interaction):
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        assert isinstance(
            self.max_guests_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        max_guests_str = self.max_guests_input.component.value

        # Validate using the validator
        validator = positive_integer_validator()
        result = validator.validate(max_guests_str)

        if not result.is_valid:
            feedback = f"**Failed to update max guests.**\n{result.error_message}"

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

        max_guests = result.value

        log.info(
            f"Setting max_guests to {max_guests} for event {self.event.event_name} ({self.event.id})"
        )

        self.event.max_guests = max_guests

        await self.update_and_respond(
            interaction=interaction,
            fields=["max_guests"],
            feedback=f"**Successfully set max guests to {max_guests}.**",
        )


class SetDepositValueButton(BaseEventFieldButton):
    """Button to update deposit value."""

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
                "Update Deposit Value" if event.deposit_value else "Set Deposit Value"
            ),
            custom_id="SetDepositValueButton",
            style=discord.ButtonStyle.primary,
        )

    def get_modal_class(self):
        return SetDepositValueModal


class SetDepositValueModal(BaseEventFieldModal):
    """Modal to set deposit value and currency."""

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
            title="Set deposit value and currency",
        )

        log.debug(
            f"current deposit_value: {event.deposit_value}, currency: {event.currency_code}"
        )

        # Deposit value input
        self.deposit_input: discord.ui.Label = discord.ui.Label(
            text="Deposit Amount",
            description="Enter the deposit amount",
            component=discord.ui.TextInput(
                placeholder=(
                    str(event.deposit_value) if event.deposit_value else "10.00"
                ),
            ),
        )

        # Currency code input
        self.currency_input: discord.ui.Label = discord.ui.Label(
            text="Currency Code",
            description="Enter currency code (e.g., GBP, USD, EUR)",
            component=discord.ui.TextInput(
                placeholder=event.currency_code or "GBP",
            ),
        )

        self.add_item(self.deposit_input)
        self.add_item(self.currency_input)

    async def on_submit(self, interaction: discord.Interaction):
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        assert isinstance(
            self.deposit_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(
            self.currency_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        deposit_str = self.deposit_input.component.value
        currency_code_str = self.currency_input.component.value

        # Validate using the currency validator
        validator = currency_validator()
        result = validator.validate((deposit_str, currency_code_str))

        if not result.is_valid:
            feedback = f"**Failed to update deposit value.**\n{result.error_message}"

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

        if not result.value:
            return

        deposit_value, currency_code = result.value

        # Get or add the currency
        async with self.client.session_factory() as session:
            currency = await self.client.service.currency.get_or_add_currency(
                currency=currency_code, session=session
            )

        log.info(
            f"Setting deposit_value to {deposit_value} ({currency_code}) for event {self.event.event_name} ({self.event.id})"
        )

        self.event.deposit_value = deposit_value
        self.event.currency_code = currency.code

        await self.update_and_respond(
            interaction=interaction,
            fields=["deposit_value", "currency_code"],
            feedback=f"**Successfully set deposit to {deposit_value:.2f} {currency_code}.**",
        )
