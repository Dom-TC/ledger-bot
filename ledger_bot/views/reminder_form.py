"""Views and Modals for interacting with reminders."""

import logging
import traceback
from typing import Any

import arrow
import discord

from ledger_bot.models import Member, Reminder, ReminderStatus, Transaction
from ledger_bot.reminder_manager import ReminderManager
from ledger_bot.services import Service
from ledger_bot.utils import (
    build_datetime,
    build_relative_datetime,
    is_valid_date,
    is_valid_time,
    is_valid_timezone,
)

log = logging.getLogger(__name__)


class FixedReminderModal(discord.ui.Modal, title="Create fixed reminder"):
    def __init__(
        self,
        service: Service,
        transaction: Transaction,
        user: discord.Member,
        member_record: Member,
        reminders: ReminderManager,
    ) -> None:
        self.service = service
        self.transaction = transaction
        self.user = user
        self.reminders = reminders
        self.member_record = member_record

        super().__init__()

        self.date: discord.ui.Label = discord.ui.Label(
            text="Reminder Date",
            description="Please enter a date as DD-MM-YYYY",
            component=discord.ui.TextInput(
                placeholder="DD-MM-YYYY",
                min_length=8,
                max_length=10,
                required=True,
            ),
        )

        self.time: discord.ui.Label = discord.ui.Label(
            text="Reminder Time",
            description="Please a time as HH:MM",
            component=discord.ui.TextInput(
                placeholder="HH:MM",
                min_length=5,
                max_length=5,
                required=True,
            ),
        )

        self.timezone: discord.ui.Label = discord.ui.Label(
            text="Timezone",
            description="You don't have a timezone stored.\nPlease add your timezone e.g. Europe/London or UTC+1",
            component=discord.ui.TextInput(
                placeholder="Europe/London",
                required=False,
            ),
        )

        self.filter: discord.ui.Label = discord.ui.Label(
            text="Set a filter (Optional)",
            description="A reminder will only be delivered if the selected status hasn't been met.",
            component=discord.ui.Select(
                placeholder="Select an option...",
                options=[
                    discord.SelectOption(
                        label=status.value.capitalize(), value=status.value
                    )
                    for status in ReminderStatus
                ],
                required=False,
            ),
        )

        self.add_item(self.date)
        self.add_item(self.time)

        log.debug(
            f"self.member_record.timezone: {self.member_record.timezone} ({type(self.member_record.timezone)})"
        )
        if not self.member_record.timezone:
            self.add_item(self.timezone)

        self.add_item(self.filter)

    async def on_submit(self, interaction: discord.Interaction):
        log.debug("FixedReminderModal submitted")

        # Tell TypeChecker about the component types
        assert isinstance(self.date.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.time.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.timezone.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.filter.component, discord.ui.Select)  # nosec B101

        date = self.date.component.value
        time = self.time.component.value
        timezone = self.timezone.component.value or None
        filter_ = (
            self.filter.component.values[0] if self.filter.component.values else None
        )

        if not is_valid_date(date):
            log.error(f"Inputed invalid date: {date}.")
            await interaction.response.send_message(
                f"Invalid date ({date}). Please try again."
            )
            return None

        if not is_valid_time(time):
            log.error(f"Inputed invalid time: {time}.")
            await interaction.response.send_message(
                f"Invalid time ({time}). Please try again."
            )
            return None

        if timezone and not is_valid_timezone(timezone):
            log.error(f"Inputed invalid timezone: {timezone}.")
            await interaction.response.send_message(
                f"Invalid timezone ({timezone}). Please try again."
            )
            return None

        if filter_:
            try:
                reminder_filter = ReminderStatus(filter_)
            except ValueError:
                log.error(f"Invalid filter: {filter_}")
                await interaction.response.send_message(
                    f"Invalid filter ({filter_}). Please try again."
                )
                return None
        else:
            reminder_filter = None

        # If timezone already stored, use that, if not store timezone
        user_set_timezone = self.member_record.timezone

        if user_set_timezone:
            timezone = user_set_timezone
        elif timezone:
            self.member_record = await self.service.member.set_timezone(
                discord_member=self.user, timezone=timezone
            )
        else:
            log.error("Timezone neither set nor provided.")
            await interaction.response.send_message(
                "Timezone neither set nor provided. Please try again."
            )
            return None

        # Convert provided time into UTC
        reminder_datetime = build_datetime(
            date_str=date,
            time_str=time,
            tz_str=timezone,
        )

        if self.transaction.id is None:
            await interaction.response.send_message(
                "Failed to find transaction ID. Please try again later."
            )
            log.error("Transaction had no record ID.")
            return

        # Create Reminder instance
        reminder = Reminder(
            reminder_date=reminder_datetime,
            member_id=self.member_record.id,
            transaction_id=self.transaction.id,
            category=reminder_filter,
        )

        log.debug(f"{reminder} / {type(reminder)}")

        log.debug(f"filter: {filter}")

        # Store reminder
        stored_reminder = await self.service.reminder.save_reminder(reminder)
        log.info(f"Successfully stored reminder {stored_reminder.id}")

        log.info("Refreshing reminders")
        await self.reminders.refresh_reminders()

        await interaction.response.send_message(
            f"Successfully stored the reminder.\nYour reminder will be scheduled for <t:{stored_reminder.reminder_date.timestamp():.0f}:f> (<t:{stored_reminder.reminder_date.timestamp():.0f}:R>)."
        )


class RelativeReminderModal(discord.ui.Modal, title="Create relative reminder"):
    def __init__(
        self,
        service: Service,
        transaction: Transaction,
        user: discord.Member,
        member_record: Member,
        reminders: ReminderManager,
    ) -> None:
        self.service = service
        self.transaction = transaction
        self.user = user
        self.reminders = reminders
        self.member_record = member_record

        super().__init__()

        self.days: discord.ui.Label = discord.ui.Label(
            text="Number of Days",
            description="How many days until the reminder?",
            component=discord.ui.TextInput(
                placeholder="01",
                required=False,
            ),
        )

        self.hours: discord.ui.Label = discord.ui.Label(
            text="Number of Hours",
            description="How many hours until the reminder?",
            component=discord.ui.TextInput(
                placeholder="00",
                required=False,
            ),
        )

        self.filter: discord.ui.Label = discord.ui.Label(
            text="Set a filter (Optional)",
            description="A reminder will only be delivered if the selected status hasn't been met.",
            component=discord.ui.Select(
                placeholder="Select an option...",
                options=[
                    discord.SelectOption(
                        label=status.value.capitalize(), value=status.value
                    )
                    for status in ReminderStatus
                ],
                required=False,
            ),
        )

        self.add_item(self.days)
        self.add_item(self.hours)

        self.add_item(self.filter)

    async def on_submit(self, interaction: discord.Interaction):
        log.debug("RelativeReminderModal submitted")

        # Tell TypeChecker about the component types
        assert isinstance(self.days.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.hours.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.filter.component, discord.ui.Select)  # nosec B101

        days = self.days.component.value or 0
        hours = self.hours.component.value or 0
        filter_ = (
            self.filter.component.values[0] if self.filter.component.values else None
        )

        if not int(days) >= 0:
            log.error(f"Inputed invalid number of days: {days}.")
            await interaction.response.send_message(
                f"Invalid number of days ({days}). Please try again."
            )
            return None

        if not int(hours) >= 0:
            log.error(f"Inputed invalid number of hours: {hours}.")
            await interaction.response.send_message(
                f"Invalid number of hours ({hours}). Please try again."
            )
            return None

        if filter_:
            try:
                reminder_filter = ReminderStatus(filter_)
            except ValueError:
                log.error(f"Invalid filter: {filter_}")
                await interaction.response.send_message(
                    f"Invalid filter ({filter_}). Please try again."
                )
                return None
        else:
            reminder_filter = None

        # If timezone already stored, use that, if not store timezone
        timezone = self.member_record.timezone or "Etc/UTC"

        # Convert provided time into UTC
        reminder_datetime = build_relative_datetime(
            days=int(days),
            hours=int(hours),
            tz_str=timezone,
        )

        if self.transaction.id is None:
            await interaction.response.send_message(
                "Failed to find transaction ID. Please try again later."
            )
            log.error("Transaction had no record ID.")
            return

        # Create Reminder instance
        reminder = Reminder(
            reminder_date=reminder_datetime,
            member_id=self.member_record.id,
            transaction_id=self.transaction.id,
            category=reminder_filter,
        )

        log.debug(f"{reminder} / {type(reminder)}")

        log.debug(f"filter: {filter}")

        # Store reminder
        stored_reminder = await self.service.reminder.save_reminder(reminder)

        log.info(f"Successfully stored reminder {stored_reminder.id}")

        log.info("Refreshing reminders")
        await self.reminders.refresh_reminders()

        await interaction.response.send_message(
            f"Successfully stored the reminder.\nYour reminder will be scheduled for <t:{stored_reminder.reminder_date.timestamp():.0f}:f> (<t:{stored_reminder.reminder_date.timestamp():.0f}:R>)."
        )


class CreateReminderButton(discord.ui.LayoutView):
    def __init__(
        self,
        service: Service,
        transaction: Transaction,
        user: discord.Member,
        buyer_user: discord.Member | discord.User,
        seller_user: discord.Member | discord.User,
        reminders: ReminderManager,
    ) -> None:
        self.service = service
        self.transaction = transaction
        self.user = user
        self.reminders = reminders
        self.buyer = buyer_user
        self.seller = seller_user

        super().__init__()

        container: discord.ui.Container = discord.ui.Container(
            discord.ui.TextDisplay(
                f'Click one of the buttons to add a reminder for "*{self.transaction.wine}*" from {self.seller.mention} to {self.buyer.mention} for £{self.transaction.price:.2f}.\nA fixed reminder will let let you input a specific date to receive a reminder.\nA relative reminder will let you set how long until the reminder goes off (in days and hours).'
            ),
        )

        row: discord.ui.ActionRow = discord.ui.ActionRow()
        fixed_button: discord.ui.Button = discord.ui.Button(
            label="Create Fixed Reminder.",
        )

        relative_button: discord.ui.Button = discord.ui.Button(
            label="Create Relative Reminder",
        )

        async def fixed_button_callback(interaction: discord.Interaction):
            member_record = await self.service.member.get_or_add_member(self.user)

            await interaction.response.send_modal(
                FixedReminderModal(
                    service=self.service,
                    transaction=self.transaction,
                    user=self.user,
                    member_record=member_record,
                    reminders=self.reminders,
                )
            )

        async def relative_button_callback(interaction: discord.Interaction):
            member_record = await self.service.member.get_or_add_member(self.user)

            await interaction.response.send_modal(
                RelativeReminderModal(
                    service=self.service,
                    transaction=self.transaction,
                    user=self.user,
                    member_record=member_record,
                    reminders=self.reminders,
                )
            )

        fixed_button.callback = fixed_button_callback  # type: ignore[method-assign]
        relative_button.callback = relative_button_callback  # type: ignore[method-assign]

        # Add buttons to row
        row.add_item(fixed_button)
        row.add_item(relative_button)

        # Add row to container
        container.add_item(row)

        # Add container to self
        self.add_item(container)
