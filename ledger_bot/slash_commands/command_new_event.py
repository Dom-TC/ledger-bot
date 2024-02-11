"""Slash command - new_event."""

import datetime
import logging
from typing import Any, Dict

import discord

from ledger_bot.date_helpers import parse_datetime
from ledger_bot.errors import DatetimeParsingError, TimeTravelError
from ledger_bot.LedgerBot import LedgerBot
from ledger_bot.models import Event
from ledger_bot.storage import EventStorage

log = logging.getLogger(__name__)


async def command_new_event(
    client: "LedgerBot",
    config: Dict[str, Any],
    storage: EventStorage,
    interaction: discord.Interaction[Any],
    event_name: str,
    event_date: str,
    max_attendees: int | None = None,
    private: bool = False,
) -> None:
    """Create a new event."""
    try:
        parsed_date = await parse_datetime(event_date, interaction.user)
        log.info(f"{event_date} parsed as {parsed_date}")
    except DatetimeParsingError:
        log.info(f'Failed to parse datetime: "{event_date}"')
        await interaction.response.send_message(
            content=f"Failed to parse {event_date} into a date / time object.",
            ephemeral=True,
        )
        return
    except TimeTravelError:
        log.info(f'Parse datetime is in past: "{event_date}"')
        await interaction.response.send_message(
            content=f"Events can't be created in the past: {event_date}.",
            ephemeral=True,
        )
        return

    if max_attendees is not None and max_attendees < 2:
        log.info(f"Max Attendees is less than 1. Skipping… ({max_attendees})")
        await interaction.response.send_message(
            content="You can't have less than two attendes.",
            ephemeral=True,
        )
        return

    event_name = event_name.strip()

    if len(event_name) < 3:
        log.info(f"Event Name is less than 3. Skipping… ({event_name})")
        await interaction.response.send_message(
            content="The event name must be at least three characters.",
            ephemeral=True,
        )
        return

    if not isinstance(interaction.user, discord.Member):
        log.error(
            f"interaction.user isn't a discord.Member. {interaction.user} / {type(interaction.user)}"
        )
        await interaction.followup.send(
            content="An unexpected error occured. Please try again later.",
            ephemeral=True,
        )
        return

    # Discord Interactions need to be responded to in <3s or they time out.  We take longer, so defer the interaction.
    await interaction.response.defer(ephemeral=True)

    # Create event object
    log.info("Processing new event...")
    log.info(f"Getting / adding host: {interaction.user}")
    host_record = await storage.get_or_add_member(interaction.user)

    event = Event(
        event_name=event_name,
        host=host_record,
        event_date=parsed_date.isoformat(),
        max_attendees=max_attendees,
        private=private,
        creation_date=datetime.datetime.utcnow().isoformat(),
    )

    # Create private channel
    channel_overwrites = {
        client.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        client.guild.me: discord.PermissionOverwrite(read_messages=True),
    }
    channel_name = (
        f"{event_name.replace(' ', '_')}_{parsed_date.strftime('%d_%b')}".lower()
    )

    try:
        event_channel = await client.guild.create_text_channel(
            name=channel_name,
            overwrites=channel_overwrites,
            category=await client.get_or_fetch_channel(config["events_category"]),
            topic=f"Event: {channel_name}",
            reason=f"Event created by {config['name']}",
        )
    except discord.Forbidden as error:
        log.error(f"A discord.Forbidden error occured creating the channel: {error}")
        await interaction.followup.send(
            "An unexpected error occured when creating the event channel.",
            ephemeral=True,
        )
        return
    except discord.HTTPException as error:
        log.error(
            f"A discord.HTTPException error occured creating the channel: {error}"
        )
        await interaction.followup.send(
            "An unexpected error occured when creating the event channel.",
            ephemeral=True,
        )
        return
    except TypeError as error:
        log.error(f"A TypeError occured creating the channel: {error}")
        await interaction.followup.send(
            "An unexpected error occured when creating the event channel.",
            ephemeral=True,
        )
        return

    event.channel_id = event_channel.id

    event_fields = [
        "event_name",
        "host",
        "event_date",
        "max_attendees",
        "private",
        "channel_id",
        "creation_date",
    ]

    event_record = await storage.save_event(event=event, fields=event_fields)

    log.debug(event_record)

    # Add host to channel
    try:
        log.info(
            f"Assigning host '{interaction.user.name}' read permission in {channel_name}"
        )
        await event_channel.set_permissions(
            interaction.user,
            read_messages=True,
        )
    except discord.Forbidden as error:
        log.error(
            f"A discord.Forbidden error occured assigning host {interaction.user.name} read access to channel {channel_name}: {error}"
        )
        await interaction.followup.send(
            "An unexpected error occured when assigning you to the event channel.",
            ephemeral=True,
        )
        return
    except discord.NotFound as error:
        log.error(
            f"A discord.NotFound error occured assigning host {interaction.user.name} read access to channel {channel_name}: {error}"
        )
        await interaction.followup.send(
            "An unexpected error occured when assigning you to the event channel.",
            ephemeral=True,
        )
    except discord.HTTPException as error:
        log.error(
            f"A discord.HTTPException error occured assigning host {interaction.user.name} read access to channel {channel_name}: {error}"
        )
        await interaction.followup.send(
            "An unexpected error occured when assigning you to the event channel.",
            ephemeral=True,
        )
        return
    except TypeError as error:
        log.error(
            f"A TypeError occured assigning host {interaction.user.name} read access to channel {channel_name}: {error}"
        )
        await interaction.followup.send(
            "An unexpected error occured when assigning you to the event channel.",
            ephemeral=True,
        )
        return
    except ValueError as error:
        log.error(
            f"A ValueError occured assigning host {interaction.user.name} read access to channel {channel_name}: {error}"
        )
        await interaction.followup.send(
            "An unexpected error occured when assigning you to the event channel.",
            ephemeral=True,
        )

    # Create buttons in channel

    return

    # # Create status post
    # response_contents = generate_event_status_message(
    #     seller=interaction.user,
    #     buyer=buyer,
    #     wine_name=wine_name,
    #     wine_price=price,
    #     config=config,
    # )
    # try:
    #     await interaction.followup.send(response_contents)

    #     # We have to call a different command to get the message we just posted
    #     bot_message = await interaction.original_response()

    #     await storage.record_bot_message(
    #         message=bot_message, transaction=transaction_record
    #     )

    # except discord.HTTPException as error:
    #     log.error(f"An error occured sending the message: {error}")
    # except discord.ClientException as error:
    #     log.error(f"Couldn't get response message channel: {error}")
    # except AirTableError as error:
    #     log.error(f"An error occured storing the content in AirTable: {error}")
