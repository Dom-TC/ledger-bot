"""DM command - dev."""

import datetime
import hashlib
import logging
import time
from typing import TYPE_CHECKING, List

import discord
from apscheduler.job import Job

from ledger_bot.commands_scheduled import cleanup, shutdown
from ledger_bot.core import register_help_command
from ledger_bot.utils import add_reaction

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def _process_shutdown_authcode(
    client: "LedgerBot",
    received_auth_code: str | None,
    message: discord.Message,
    dm_channel: discord.DMChannel,
) -> str:
    """Handle the provided shutdown authcode.

    Parameters
    ----------
    client : LedgerBot
        The bot instance
    received_auth_code : str | None
        The auth code provided by the user, if any.
    message : discord.Message
        The discord message object that triggered the command.
    dm_channel : discord.DMChannel
        The DM channel of the user who triggered the command

    Returns
    -------
    str
        The message to return to the user
    """
    now = int(time.time())
    window_duration = 120  # Window to every 2 minutes
    window = now // window_duration
    expiry = now + (window_duration - (now % window_duration))

    token_input = f"{client.version}:{window}".encode()
    token_hash = hashlib.sha256(token_input).hexdigest().upper()

    auth_code = f"{token_hash[:4]}-{token_hash[4:8]}"

    log.debug(f"Received auth code: {received_auth_code}")
    log.debug(f"Required auth code: {auth_code}")

    if received_auth_code is None:
        response = (
            f"To shutdown {client.config.name}, please use the following command:\n"
        )
        response += f"`!dev shutdown {auth_code}`\n"
        response += f"The code expires <t:{expiry}:R>\n"
        response += "\n"
        response += "⚠️⚠️⚠️"
        response += "\n"
        response += "This cannot be undone.\n"
        response += (
            f"The only way to restart {client.config.name} is via a deployment.\n"
        )
        response += "⚠️⚠️⚠️"
        response += "\n"

        return response

    if received_auth_code == auth_code:
        log.info(f"Received valid shutdown code from {message.author.name}.")

        shutdown_time = datetime.datetime.now(
            datetime.timezone.utc
        ) + datetime.timedelta(minutes=client.config.shutdown_delay)
        shutdown_ts = int(shutdown_time.timestamp())

        client.scheduler.add_job(
            func=shutdown,
            trigger="date",
            run_date=shutdown_time,
            kwargs={"client": client, "dm_channel": dm_channel},
            id="shutdown",
            name="Shutdown",
        )

        response = "Received valid shutdown command.\n"
        response += (
            f"Shutdown will commence at <t:{shutdown_ts}:t> (<t:{shutdown_ts}:R>).\n"
        )
        response += "Use `!dev cancel_shutdown` to cancel."

        return response

    else:
        log.info("Received invalid shutdown code.")

        response = "Invalid code. Please try again.\n"
        response += "\n"
        response += (
            f"To shutdown {client.config.name}, please use the following command:\n"
        )
        response += f"`!dev shutdown {auth_code}`\n"
        response += f"The code expires <t:{expiry}:R>\n"
        response += "\n"
        response += "⚠️⚠️⚠️"
        response += "\n"
        response += "This cannot be undone.\n"
        response += (
            f"The only way to restart {client.config.name} is via a deployment.\n"
        )
        response += "⚠️⚠️⚠️"
        response += "\n"

        return response


@register_help_command(
    command="dev add_reaction",
    args=["message_id", "reaction"],
    description="Applies the specified reaction to the given message.",
    requires_dev=True,
    scope="dm",
)
@register_help_command(
    command="dev get_jobs",
    description="Returns a list of the currently scheduled jobs.",
    requires_dev=True,
    scope="dm",
)
@register_help_command(
    command="dev clean",
    description="Cleans completed transactions older than {config.cleanup_delay_hours}.",
    requires_dev=True,
    scope="dm",
)
@register_help_command(
    command="dev refresh_reminders",
    description="Refreshes the scheduled reminders.",
    requires_dev=True,
    scope="dm",
)
@register_help_command(
    command="dev refresh_message",
    args=["transaction_row_id", "optional: channel_id"],
    description="Deletes all existing messages for a given transaction, and posts a new status update.",
    requires_dev=True,
    scope="dm",
)
@register_help_command(
    command="dev shutdown",
    args=["optional: confirmation_token"],
    description="Shutdown {config.name}, requires a confirmation token that will be displayed when first run.",
    requires_dev=True,
    scope="dm",
)
@register_help_command(
    command="dev cancel_shutdown",
    description="Cancels the scheduled shutdown.",
    requires_dev=True,
    scope="dm",
)
@register_help_command(
    command="dev welcome_back",
    description="Posts a message saying ledger_bot is running again.",
    requires_dev=True,
    scope="dm",
)
async def command_dev(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - dev."""
    message_content = message.content.lower().strip()

    request = message_content.removeprefix("!dev ")
    log.info(f"Processing dev mode request ({request}) from {message.author.name}")

    if request.startswith("add_reaction"):
        message_id = int(request.split(" ")[1])
        reaction = request.split(" ")[2]

        await add_reaction(client, message_id, reaction)

    elif request.startswith("get_jobs"):
        jobs: List[Job] = client.scheduler.get_jobs()

        if len(jobs) == 0:
            result = "There are no jobs currently configured."
        else:
            result = "The following jobs are currently configured: \n"
            for job in jobs:
                assert isinstance(job.next_run_time, datetime.datetime)  # nosec B101
                result += f"- {job.id}: {job.name} - {job.trigger} {job.next_run_time} (Next running: <t:{job.next_run_time.timestamp():.0f}:f>)\n"

        await dm_channel.send(result)

    elif request.startswith("clean"):
        await dm_channel.send("Cleaning records")
        await cleanup(client=client, service=client.service)

    elif request.startswith("refresh_reminders"):
        await dm_channel.send("Refreshing reminders")
        await client.reminders.refresh_reminders()

    elif request.startswith("refresh_message"):
        display_id = int(request.split(" ")[1])
        channel_id = int(request.split(" ")[2]) if len(request.split(" ")) > 2 else None
        await dm_channel.send(f"Refreshing transaction: {display_id}")
        response = await client.refresh_transaction(
            display_id=display_id, channel_id=channel_id
        )
        await dm_channel.send(response)

    if request.startswith("shutdown"):
        log.info("Received shutdown command")
        parts = request.split(" ", 1)  # Split at most once
        received_auth_code = parts[1].upper() if len(parts) > 1 else None

        response = await _process_shutdown_authcode(
            client=client,
            received_auth_code=received_auth_code,
            message=message,
            dm_channel=dm_channel,
        )

        await dm_channel.send(response)

    if request.startswith("cancel_shutdown"):
        job = client.scheduler.get_job("shutdown")
        if job:
            log.debug(f"Removing job {job}")
            job.remove()
            await dm_channel.send("Shutdown has been cancelled.")

    if request.startswith("welcome_back"):
        log.info("Sending welcome back message")

        if client.config.channels.shutdown_post_channel is not None:
            channel = await client.get_or_fetch_channel(
                client.config.channels.shutdown_post_channel
            )
            if channel is not None and isinstance(channel, discord.TextChannel):
                msg = f"<@{client.user.id if client.user else None}> has been restarted.  Full service has resumed.\n"
                msg += f"-# Version: {client.version}"

                if bot_id := client.config.bot_id:
                    msg = f"{msg} ({bot_id})"

                msg += "\n"
                msg += f"-# Latency: {(client.latency * 1000):.3f}ms"

                await channel.send(msg)

                response = (
                    f"Successfully posted welcome back message in {channel.jump_url}."
                )

            else:
                log.warning(
                    "`client.config.shutdown_post_channel` did not return an id for a valid discord.TextChannel"
                )
                response = "Failed to post welcome back message"

            await dm_channel.send(response)
