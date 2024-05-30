"""Views and Modals for interacting with events."""

import logging
import traceback
from typing import Any

import arrow
import discord

from ledger_bot.models import Event
from ledger_bot.storage import EventStorage

log = logging.getLogger(__name__)


class ManageEventButton(discord.ui.View):
    def __init__(
        self,
        storage: EventStorage,
        event: Event,
        host: discord.Member,
    ) -> None:
        self.storage = storage
        self.event = event
        self.host = host

        super().__init__()

    @discord.ui.button(label="Create Reminder")
    async def set_time(
        self, interaction: discord.Interaction[Any], button: discord.ui.Button[Any]
    ) -> None:
        await interaction.response.send_message("Button Acknowledged")
