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

    async with client.session_factory() as session:
        event_record = await client.service.event.get_event(event.id, session)

        event = event_record if event_record else event

        header_string = "*New Event!*"

        description_string = (
            f"{event.event_description}\n" if event.event_description else ""
        )

        # Create comma seperated list, with "and" before final element
        log.debug(event)
        if len(event.hosts) > 1:
            hosts = (
                "<@"
                + ">, <@".join(str(host.member.discord_id) for host in event.hosts[:-1])
                + ">, and <@"
                + str(event.hosts[-1].member.discord_id)
                + ">"
            )
        else:
            hosts = f"<@{str(event.hosts[0].member.discord_id)}>"

        date_string = str(
            event.event_date.strftime(
                f"%H:%M, %A, %d{get_ordinal_suffix(event.event_date.day)} %B %Y"
            )
            if event.event_date
            else "Ongoing" if event.is_ongoing else "TBD"
        )

        location_string = (
            f"Location: {event.event_location}\n" if event.event_location else ""
        )

        if event.max_guests and not event.is_full:
            has_space_string = f"There are currently {event.max_guests - event.guest_count}/{event.max_guests} spaces remaining. Sign up below."
        elif not event.is_full:
            has_space_string = "There are spaces available. Sign up below."
        else:
            has_space_string = (
                "The event is currently full, but join the waitlist below."
            )

    message_contents = (
        f"{header_string}\n"
        f"**{event.event_name}**\n"
        f"{description_string}"
        "\n"
        f"{pluralise_word(len(event.hosts), "Host")}: {hosts}\n"
        f"Date: {date_string}\n"
        f"{location_string}"
        f"{has_space_string}\n"
    )

    return message_contents
