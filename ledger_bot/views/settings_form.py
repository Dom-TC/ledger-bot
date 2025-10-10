"""Views and Modals for interacting with reminders."""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import discord

from ledger_bot.models import Member
from ledger_bot.utils import build_datetime, is_valid_timezone

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class LookupEnabledButton(discord.ui.Button):
    def _label(self):
        return "Disable Lookup" if self.requestor.lookup_enabled else "Enable Lookup"

    def _style(self):
        return (
            discord.ButtonStyle.success
            if self.requestor.lookup_enabled
            else discord.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        self.requestor.lookup_enabled = not self.requestor.lookup_enabled

        self.requestor = await self.client.service.member.update_member(
            self.requestor, ["lookup_enabled"]
        )

        self.label = self._label()
        self.style = self._style()

        await interaction.response.edit_message(view=self.view)

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
    ) -> None:
        self.client = client
        self.requestor = requestor

        super().__init__(
            label=self._label(),
            style=self._style(),
            custom_id="LookupEnabledButton",
        )


class SetTimezoneButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            SetTimezoneModal(client=self.client, requestor=self.requestor)
        )

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
    ) -> None:
        self.client = client
        self.requestor = requestor

        super().__init__(
            label="Set Timezone",
            style=discord.ButtonStyle.primary,
            custom_id="SetTimezoneButton",
        )


class SetTimezoneModal(discord.ui.Modal, title="Set your timezone"):
    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
    ) -> None:
        self.client = client
        self.requestor = requestor

        super().__init__()

        log.debug(f"current timezone: {requestor.timezone}")

        self.timezone: discord.ui.Label = discord.ui.Label(
            text="Timezone",
            description="Please add your timezone e.g. Europe/London or UTC+1",
            component=discord.ui.TextInput(
                placeholder=requestor.timezone,
            ),
        )

        self.add_item(self.timezone)

    async def on_submit(self, interaction: discord.Interaction):
        # Tell TypeChecker about the component types
        assert isinstance(self.timezone.component, discord.ui.TextInput)  # nosec B101
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101

        tz = self.timezone.component.value

        log.debug(
            f"Storing timezone {tz} for member {self.requestor.username} ({self.requestor.id})"
        )

        if not is_valid_timezone(tz):
            log.error(f"Inputed invalid timezone: {tz}.")
            await interaction.response.send_message(
                f"Invalid timezone ({tz}). Please try again.", ephemeral=True
            )
            return None

        discord_member = await self.client.get_or_fetch_member(
            self.requestor.discord_id, self.client.guild
        )
        self.requestor = await self.client.service.member.set_timezone(
            discord_member=discord_member, timezone=tz
        )

        current_time = datetime.now(timezone.utc).astimezone(
            self.requestor.resolve_timezone
        )

        feedback = (
            f"**Successfully updated timezeone.**\n"
            f"It is currently `{current_time.strftime("%H:%M")}` in `{tz}`"
        )

        await interaction.response.send_message(
            view=CreateSettingsButtons(
                client=self.client, requestor=self.requestor, feedback=feedback
            ),
        )


class CreateSettingsButtons(discord.ui.LayoutView):
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
            discord.ui.TextDisplay("# User Settings")
        )

        user_settings_row: discord.ui.ActionRow = discord.ui.ActionRow()

        set_lookup_enabled_button = LookupEnabledButton(
            client=client,
            requestor=requestor,
        )

        set_timezone_button = SetTimezoneButton(
            client=client,
            requestor=requestor,
        )

        # Add buttons to row
        user_settings_row.add_item(set_lookup_enabled_button)
        user_settings_row.add_item(set_timezone_button)

        # Add rows to containers
        user_settings_container.add_item(user_settings_row)

        # Add containers to self
        if self.feedback:
            self.add_item(feedback_container)

        self.add_item(user_settings_container)
