"""Views and Modals for hosts interacting with events."""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import discord

from ledger_bot.errors import EventChannelError
from ledger_bot.models import Event, EventMember, EventMemberStatus, Member
from ledger_bot.utils import build_datetime, is_valid_timezone

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class SetNameButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetNameModal(client=self.client, requestor=self.requestor, event=self.event)
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
            label="Update Event Name",
            style=discord.ButtonStyle.primary,
            custom_id="SetNameButton",
        )


class SetNameModal(discord.ui.Modal, title="Set the event name"):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

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
        # Tell TypeChecker about the component types
        assert isinstance(self.name_input.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        new_name = self.name_input.component.value
        old_name = self.event.event_name

        log.info(f"Storing event name {new_name} for event {self.event.id}")

        self.event.event_name = new_name
        self.event = await self.client.service.event.update_event(
            event=self.event,
            fields=["event_name"],
        )
        try:
            await self.client.update_channel_name(event=self.event)

        except EventChannelError:
            log.error("Failed to update event channel name")

            self.event.event_name = old_name
            self.event = await self.client.service.event.update_event(
                event=self.event,
                fields=["event_name"],
            )

            feedback = "**Failed to update event name.**\nAn unexpected error occured."

        else:
            feedback = "**Successfully updated event name.**"

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class SetDescriptionButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetDescriptionModal(
                client=self.client, requestor=self.requestor, event=self.event
            )
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
            label=(
                "Update Event Description"
                if self.event.event_description
                else "Set Event Description"
            ),
            style=discord.ButtonStyle.primary,
            custom_id="SetDescriptionButton",
        )


class SetDescriptionModal(discord.ui.Modal, title="Set the event description"):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

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
        # Tell TypeChecker about the component types
        assert isinstance(
            self.description_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        description = self.description_input.component.value

        log.info(
            f"Storing event description {description} for event {self.event.event_name} ({self.event.id})"
        )

        self.event.event_description = description
        self.event = await self.client.service.event.update_event(
            event=self.event,
            fields=["event_description"],
        )

        feedback = "**Successfully updated event description.**"

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class SetLocationButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetLocationModal(
                client=self.client, requestor=self.requestor, event=self.event
            )
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
            label=(
                "Update Event Location"
                if self.event.event_location
                else "Set Event Location"
            ),
            style=discord.ButtonStyle.primary,
            custom_id="SetLocationButton",
        )


class SetLocationModal(discord.ui.Modal, title="Set the event location"):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

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
        # Tell TypeChecker about the component types
        assert isinstance(
            self.description_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        location = self.description_input.component.value

        log.info(
            f"Storing event location {location} for event {self.event.event_name} ({self.event.id})"
        )

        self.event.event_location = location
        self.event = await self.client.service.event.update_event(
            event=self.event,
            fields=["event_location"],
        )

        feedback = "**Successfully updated event location.**"

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class SetDateButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetDateModal(client=self.client, requestor=self.requestor, event=self.event)
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
            label="Update Event Date" if self.event.event_date else "Set Event Date",
            style=(
                discord.ButtonStyle.success
                if self.event.event_date
                else discord.ButtonStyle.secondary
            ),
            custom_id="SetDateButton",
        )


class SetDateModal(discord.ui.Modal, title="Set specific event date"):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

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
        # Fetch the latest event from the database to avoid stale data
        async with self.client.session_factory() as session:
            self.event = await self.client.service.event.get_event(
                record_id=self.event.id, session=session
            )

        if self.event is None:
            await interaction.response.send_message(
                "**Failed to update event date.**\nEvent not found.",
            )
            return

        # Tell TypeChecker about the component types
        assert isinstance(self.date_input.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.time_input.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        date_str = self.date_input.component.value.strip()
        time_str = self.time_input.component.value.strip()
        timezone_str = "UTC"

        # Store old values for rollback if needed
        old_event_date = self.event.event_date
        old_is_ongoing = self.event.is_ongoing
        event_datetime = self.event.event_date

        # Parse and set the date
        try:
            # Parse the date and time
            event_datetime = build_datetime(
                date_str=date_str,
                time_str=time_str if time_str else "00:00",
                tz_str=timezone_str,
            )

            log.info(
                f"Setting event date to {event_datetime} for event {self.event.event_name} ({self.event.id})"
            )

            self.event.event_date = event_datetime
            self.event.is_ongoing = False

        except ValueError as e:
            feedback = (
                f"**Failed to update event date.**\n"
                f"Invalid date or time format: {str(e)}\n"
                f"Please use YYYY-MM-DD for date and HH:MM for time."
            )
            await interaction.response.send_message(
                view=CreateEventManagementButtons(
                    client=self.client,
                    requestor=self.requestor,
                    feedback=feedback,
                    event=self.event,
                ),
            )
            return

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

            feedback = "**Failed to update event date.**\nAn unexpected error occurred."

        else:
            feedback = f"**Successfully set event date to {event_datetime.strftime('%Y-%m-%d %H:%M %Z')}.**"

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class SetOngoingButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        # Fetch the latest event from the database to avoid stale data
        if not self.event:
            return

        async with self.client.session_factory() as session:
            self.event = await self.client.service.event.get_event(
                record_id=self.event.id, session=session
            )

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

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
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


class SetTBDButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        # Fetch the latest event from the database to avoid stale data
        if not self.event:
            return

        async with self.client.session_factory() as session:
            self.event = await self.client.service.event.get_event(
                record_id=self.event.id, session=session
            )

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

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
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


class SetMaxGuestsButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetMaxGuestsModal(
                client=self.client, requestor=self.requestor, event=self.event
            )
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
            label="Update Max Guests" if self.event.max_guests else "Set Max Guests",
            style=discord.ButtonStyle.primary,
            custom_id="SetMaxGuestsButton",
        )


class SetMaxGuestsModal(discord.ui.Modal, title="Set maximum number of guests"):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

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
        # Tell TypeChecker about the component types
        assert isinstance(
            self.max_guests_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        max_guests_str = self.max_guests_input.component.value.strip()

        try:
            max_guests = int(max_guests_str)
            if max_guests <= 0:
                raise ValueError("Max guests must be a positive number")

            log.info(
                f"Setting max_guests to {max_guests} for event {self.event.event_name} ({self.event.id})"
            )

            self.event.max_guests = max_guests
            self.event = await self.client.service.event.update_event(
                event=self.event,
                fields=["max_guests"],
            )

            feedback = f"**Successfully set max guests to {max_guests}.**"

        except ValueError:
            feedback = (
                "**Failed to update max guests.**\n"
                "Please enter a valid positive number."
            )

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class SetDepositValueButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetDepositValueModal(
                client=self.client, requestor=self.requestor, event=self.event
            )
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
            label=(
                "Update Deposit Value"
                if self.event.deposit_value
                else "Set Deposit Value"
            ),
            style=discord.ButtonStyle.primary,
            custom_id="SetDepositValueButton",
        )


class SetDepositValueModal(discord.ui.Modal, title="Set deposit value and currency"):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

        log.debug(
            f"current deposit_value: {event.deposit_value}, currency: {event.currency_code}"
        )

        # Deposit value input
        self.deposit_input: discord.ui.Label = discord.ui.Label(
            text="Deposit Amount",
            description="Enter the deposit amount",
            component=discord.ui.TextInput(
                placeholder=(
                    str(event.deposit_value / 100) if event.deposit_value else "10.00"
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
        # Tell TypeChecker about the component types
        assert isinstance(
            self.deposit_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(
            self.currency_input.component, discord.ui.TextInput
        )  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        deposit_str = self.deposit_input.component.value.strip()
        currency_code_str = self.currency_input.component.value.strip().upper()

        try:
            # Validate and parse deposit value
            deposit_value = float(deposit_str)
            if deposit_value < 0:
                raise ValueError("Deposit value must be non-negative")

            # Convert to cents/pennies (store as integer)
            deposit_value_cents = int(deposit_value * 100)

            # Get or add the currency
            async with self.client.session_factory() as session:
                currency = await self.client.service.currency.get_or_add_currency(
                    currency=currency_code_str, session=session
                )

            log.info(
                f"Setting deposit_value to {deposit_value_cents} ({currency_code_str}) for event {self.event.event_name} ({self.event.id})"
            )

            self.event.deposit_value = deposit_value_cents
            self.event.currency_code = currency.code
            self.event = await self.client.service.event.update_event(
                event=self.event,
                fields=["deposit_value", "currency_code"],
            )

            feedback = f"**Successfully set deposit to {deposit_value:.2f} {currency_code_str}.**"

        except ValueError:
            feedback = (
                "**Failed to update deposit value.**\n"
                "Please enter a valid number for the deposit amount."
            )

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class AddMemberButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=AddMemberView(
                client=self.client, requestor=self.requestor, event=self.event
            ),
            ephemeral=True,
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
            label="Add Member",
            style=discord.ButtonStyle.primary,
            custom_id="AddMemberButton",
        )


class AddMemberView(discord.ui.View):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

        # Add user select
        user_select = discord.ui.UserSelect(
            placeholder="Select a user to add as a member",
            min_values=1,
            max_values=1,
        )
        user_select.callback = self.user_selected
        self.add_item(user_select)

    async def user_selected(self, interaction: discord.Interaction):
        # Get the selected user from the select component
        # The interaction will have the UserSelect component with selected values
        select_data = interaction.data.get("values", []) if interaction.data else []  # type: ignore

        if not select_data:
            await interaction.response.send_message(
                "**Failed to add member.**\nNo user selected.",
                ephemeral=True,
            )
            return

        user_id = int(select_data[0])

        # Get the user from the guild
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101
        user = self.client.guild.get_member(user_id)

        if user is None:
            await interaction.response.send_message(
                "**Failed to add member.**\nUser not found in the server.",
                ephemeral=True,
            )
            return

        # Get or create the member record
        async with self.client.session_factory() as session:
            member = await self.client.service.member.get_or_add_member(
                user, session=session
            )

            # Check if the user is already a member of this event
            existing_members = (
                await self.client.service.event_member.list_event_members_by_event(
                    event_id=self.event.id, session=session
                )
            )

            # Check if member is already in the event
            is_already_member = any(
                em.member_id == member.id for em in existing_members
            )

            if is_already_member:
                feedback = f"**{user.display_name} is already a member of this event.**"
            else:
                # Add the member to the event
                event_member = EventMember(
                    event_id=self.event.id,
                    member_id=member.id,
                    status=EventMemberStatus.CONFIRMED,
                    bot_id=self.client.guild.id,
                )
                await self.client.service.event_member.add_event_member(
                    event_member=event_member, session=session
                )

                log.info(
                    f"Added {user.display_name} (member_id: {member.id}) to event {self.event.event_name} ({self.event.id}) as CONFIRMED"
                )

                feedback = f"**Successfully added {user.display_name} as a member.**"

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class AddHostButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=AddHostView(
                client=self.client, requestor=self.requestor, event=self.event
            ),
            ephemeral=True,
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
            label="Add Host",
            style=discord.ButtonStyle.primary,
            custom_id="AddHostButton",
        )


class AddHostView(discord.ui.View):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

        # Add user select
        user_select = discord.ui.UserSelect(
            placeholder="Select a user to add as a host",
            min_values=1,
            max_values=1,
        )
        user_select.callback = self.user_selected
        self.add_item(user_select)

    async def user_selected(self, interaction: discord.Interaction):
        # Get the selected user from the select component
        # The interaction will have the UserSelect component with selected values
        select_data = interaction.data.get("values", []) if interaction.data else []  # type: ignore

        if not select_data:
            await interaction.response.send_message(
                "**Failed to add host.**\nNo user selected.",
                ephemeral=True,
            )
            return

        user_id = int(select_data[0])

        # Get the user from the guild
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101
        user = self.client.guild.get_member(user_id)

        if user is None:
            await interaction.response.send_message(
                "**Failed to add host.**\nUser not found in the server.",
                ephemeral=True,
            )
            return

        # Get or create the member record
        async with self.client.session_factory() as session:
            member = await self.client.service.member.get_or_add_member(
                user, session=session
            )

            # Check if the user is already a member of this event
            existing_members = (
                await self.client.service.event_member.list_event_members_by_event(
                    event_id=self.event.id, session=session
                )
            )

            # Check if member is already in the event
            existing_event_member = next(
                (em for em in existing_members if em.member_id == member.id), None
            )

            if existing_event_member:
                # Update their status to HOST
                existing_event_member.status = EventMemberStatus.HOST
                await self.client.service.event_member.update_event_member(
                    event_member=existing_event_member,
                    fields=["status"],
                    session=session,
                )

                log.info(
                    f"Updated {user.display_name} (member_id: {member.id}) to HOST for event {self.event.event_name} ({self.event.id})"
                )

                feedback = f"**Successfully updated {user.display_name} to host.**"
            else:
                # Add the member to the event as a host
                event_member = EventMember(
                    event_id=self.event.id,
                    member_id=member.id,
                    status=EventMemberStatus.HOST,
                    bot_id=self.client.guild.id,
                )
                await self.client.service.event_member.add_event_member(
                    event_member=event_member, session=session
                )

                log.info(
                    f"Added {user.display_name} (member_id: {member.id}) to event {self.event.event_name} ({self.event.id}) as HOST"
                )

                feedback = f"**Successfully added {user.display_name} as a host.**"

        await interaction.response.send_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
            ),
        )


class ToggleIsPrivateButton(discord.ui.Button):
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
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
        feedback: str | None = None,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.feedback = feedback
        self.event = event

        super().__init__()

        feedback_container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay(self.feedback or "")
        )

        event_management_container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay("# Event Management")
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
            )

            await interaction.followup.send(
                view=management_view,
                ephemeral=True,
            )
