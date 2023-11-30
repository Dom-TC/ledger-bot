"""Views and Modals for interacting with reminders."""

import logging
import traceback
from typing import Optional

import arrow
import discord

from ledger_bot.models import Reminder, Transaction
from ledger_bot.reminder_manager import ReminderManager
from ledger_bot.storage import AirtableStorage

log = logging.getLogger(__name__)


class StoreReminderButton(discord.ui.Button["SetFilterView"]):
    def __init__(self, label: str):
        super().__init__(label=label)

    async def callback(self, interaction: discord.Interaction):
        # Get the reminder from the parent view
        assert self.view is not None
        view: SetFilterView = self.view

        log.debug(f"Creating reminder {view.reminder}")
        await view.reminder_manager.create_reminder(reminder=view.reminder)
        await interaction.response.send_message("Successfully added reminder!")


class StatusDropdown(discord.ui.Select):
    def __init__(self):
        # Set the options that will be presented inside the dropdown
        options = [
            discord.SelectOption(label="Approved"),
            discord.SelectOption(label="Cancelled"),
            discord.SelectOption(label="Completed"),
            discord.SelectOption(label="Delivered"),
            discord.SelectOption(label="Paid"),
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(
            placeholder="Select a filter (Optional)",
            min_values=0,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Set the status paramater of the reminder instance stored in the parent view to the value of the selection
        assert self.view is not None
        view: SetFilterView = self.view
        status_value = self.values[0].lower()
        view.reminder.status = status_value
        log.debug(f"Setting status of {view.reminder} to {status_value}")

        await interaction.response.defer()


class SetFilterView(discord.ui.View):
    def __init__(
        self,
        storage: AirtableStorage,
        reminder: Reminder,
        reminder_manager: ReminderManager,
    ) -> None:
        self.reminder = reminder
        self.storage = storage
        self.reminder_manager = reminder_manager

        super().__init__()

        self.add_item(StatusDropdown())
        self.add_item(StoreReminderButton(label="Save Reminder"))


class ReminderForm(discord.ui.Modal, title="Create Reminder In..."):
    def __init__(
        self,
        storage: AirtableStorage,
        transaction: Transaction,
        user: discord.Member,
        reminders: ReminderManager,
    ) -> None:
        self.storage = storage
        self.transaction = transaction
        self.user = user
        self.reminders = reminders

        super().__init__()

    days = discord.ui.TextInput(label="Days", required=False)
    hours = discord.ui.TextInput(label="Hours", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        # hours and days need to be ints
        try:
            hours = int(self.hours.value)
        except ValueError:
            hours = 0

        try:
            days = int(self.days.value)
        except ValueError:
            days = 0

        if not (hours or days):
            await interaction.response.send_message(
                "Please specify either a number of hours or days."
            )
            return

        # Parse time
        creation_time = arrow.utcnow()
        reminder_time = creation_time.shift(hours=+hours, days=+days)
        display_time = int(reminder_time.timestamp())

        member_record = await self.storage.get_or_add_member(self.user)

        if self.transaction.record_id is None:
            await interaction.response.send_message(
                "Failed to find transaction ID. Please try again later."
            )
            log.error("Transaction had no record ID.")
            return

        # Create Reminder instance
        self.reminder = Reminder(
            date=reminder_time.datetime,
            member_id=member_record.record_id,
            transaction_id=self.transaction.record_id,
        )

        log.debug(f"{self.reminder} / {type(self.reminder)}")

        await interaction.response.send_message(
            content=f"Your reminder will be scheduled for <t:{display_time}:f> (<t:{display_time}:R>).\nWould you like to add a filter? The reminder will only be sent if the filter **hasn't** been met.\nPress Save to confirm your reminder.",
            view=SetFilterView(
                storage=self.storage,
                reminder=self.reminder,
                reminder_manager=self.reminders,
            ),
        )

        # Send message with time, allowing user to add a filter.
        # If they confirm, add to storage
        # Schedule first reminder

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        traceback.print_exception(type(error), error, error.__traceback__)


class CreateReminderButton(discord.ui.View):
    def __init__(
        self,
        storage: AirtableStorage,
        transaction: Transaction,
        user: discord.Member,
        reminders: ReminderManager,
    ) -> None:
        self.storage = storage
        self.transaction = transaction
        self.user = user
        self.reminders = reminders

        super().__init__()

    @discord.ui.button(label="Create Reminder")
    async def set_time(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            ReminderForm(
                storage=self.storage,
                transaction=self.transaction,
                user=self.user,
                reminders=self.reminders,
            )
        )
