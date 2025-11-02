"""Generate a signup message for a given event."""

import logging
from typing import TYPE_CHECKING

from ledger_bot.models import Event
from ledger_bot.utils import get_ordinal_suffix

from .helpers import pluralise_word

if TYPE_CHECKING:
    from ledger_bot.clients import EventClient

log = logging.getLogger(__name__)


async def generate_event_signup_message(event: Event, client: "EventClient") -> str:
    """
    Generates the text for displaying an event signup.

    Paramaters
    ----------
    event: Event
        The event
    client: EventClient,
        The client posting the message

    Returns
    -------
    str
        The string of the message to be posted

    """
    log.info("Generating event detail message...")
    return "Message Generator not implemented yet."
