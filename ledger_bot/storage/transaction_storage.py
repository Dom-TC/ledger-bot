"""The various models used by ledger-bot."""

import logging

from .bot_messages_mixin import BotMessagesMixin
from .members_mixin import MembersMixin
from .reminders_mixin import RemindersMixin
from .transactions_mixin import TransactionsMixin

log = logging.getLogger(__name__)


class TransactionStorage(
    RemindersMixin, BotMessagesMixin, TransactionsMixin, MembersMixin
):
    """
    A class to interface with AirTable.

    Attributes
    ----------
    airtable_key : str
        The authentication key to connect to the base
    bot_id : str
        The id of ledger-bot
    users_url : str
        The endpoint for the users table
    wines_url : str
        The endpoint for the wines table
    bot_messages_url : str
        The endpoint for the bot_messages table
    auth_header :
        The authentication header

    """

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
