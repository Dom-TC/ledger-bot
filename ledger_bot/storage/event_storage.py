"""The various functions for dealing with event storage."""

import logging

from .mixins import (
    BaseStorage,
    EventDepositsMixin,
    EventsMixin,
    EventWinesMixin,
    MembersMixin,
)

log = logging.getLogger(__name__)


class EventStorage(
    EventDepositsMixin, EventWinesMixin, EventsMixin, MembersMixin, BaseStorage
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
        self.events_url = f"https://api.airtable.com/v0/{airtable_base}/events"
        self.event_wines_url = (
            f"https://api.airtable.com/v0/{airtable_base}/event_wines"
        )
        self.event_deposits_url = (
            f"https://api.airtable.com/v0/{airtable_base}/event_deposits"
        )
