"""The various models used by ledger-bot."""

import logging

from .mixins import (
    BaseStorage,
    BotMessagesMixin,
    MembersMixin,
    RemindersMixin,
    TransactionsMixin,
)

log = logging.getLogger(__name__)


class TransactionStorage(
    RemindersMixin, BotMessagesMixin, TransactionsMixin, MembersMixin, BaseStorage
):
    """A class to interface with AirTable."""

    def __init__(
        self,
        airtable_base: str,
        airtable_key: str,
        bot_id: str,
    ):
        super().__init__(airtable_base, airtable_key)
        self.airtable_key = airtable_key
        self.bot_id = bot_id
        self.members_url = f"https://api.airtable.com/v0/{airtable_base}/members"
        self.wines_url = f"https://api.airtable.com/v0/{airtable_base}/wines"
        self.bot_messages_url = (
            f"https://api.airtable.com/v0/{airtable_base}/bot_messages"
        )
        self.reminders_url = f"https://api.airtable.com/v0/{airtable_base}/reminders"
