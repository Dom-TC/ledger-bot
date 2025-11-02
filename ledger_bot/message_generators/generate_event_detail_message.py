"""Generate a detail message for a given event."""

import logging
from typing import TYPE_CHECKING

from ledger_bot.models import Event
from ledger_bot.utils import get_ordinal_suffix

from .helpers import pluralise_word

if TYPE_CHECKING:
    from ledger_bot.clients import EventClient

log = logging.getLogger(__name__)


async def generate_event_detail_message(event: Event, client: "EventClient") -> str:
    """
    Generates the text for displaying an event detail.

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

        guests_string = (
            f"{event.guest_count} / {event.max_guests}"
            if event.max_guests
            else f"{event.guest_count}"
        )

        deposit_string = (
            f"Deposit: {event.currency.symbol}{event.deposit_value}\n"
            if event.deposit_value
            else ""
        )

        is_private_string = (
            "This event is invite only and won't be publicly advertised.\n"
            if event.is_private
            else ""
        )

    message_contents = (
        f"# {event.event_name}\n"
        f"{description_string}"
        "\n"
        f"{pluralise_word(len(event.hosts), "Host")}: {hosts}\n"
        f"Date: {date_string}\n"
        f"{location_string}"
        "\n"
        f"{deposit_string}"
        f"Attendees: {guests_string}\n"
        "\n"
        f"{is_private_string}"
    )

    return message_contents
