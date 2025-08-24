"""The various models used by ledger-bot."""

import logging

from .mixins import BotMessagesMixin, MembersMixin, RemindersMixin, TransactionsMixin

log = logging.getLogger(__name__)


class AirtableStorage(
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

    Methods
    -------
    insert_member(record, session)
        Creates a new member entry

    get_or_add_member(member)
        Either returns the record for the given member, or creates an entry and returns that

    insert_transaction(record, session)
        Creates a new transaction entry

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
