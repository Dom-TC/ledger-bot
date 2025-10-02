"""DM command - dev."""

import datetime
import hashlib
import logging
import time
from typing import TYPE_CHECKING

import discord

from ledger_bot.commands_scheduled import cleanup, shutdown
from ledger_bot.reactions import add_reaction

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


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
        jobs = client.scheduler.get_jobs()

        if len(jobs) == 0:
            result = "There are no jobs currently configured."
        else:
            result = "The following jobs are currently configured: \n"
            for job in jobs:
                result += (
                    f"- {job.id}: {job.name} - {job.trigger} {job.next_run_time}\n"
                )

        await dm_channel.send(result)

    elif request.startswith("clean"):
        await dm_channel.send("Cleaning records")
        await cleanup(client=client, service=client.service)

    elif request.startswith("refresh_reminders"):
        await dm_channel.send("Refreshing reminders")
        await client.reminders.refresh_reminders()

    elif request.startswith("refresh_message"):
        record_id = int(request.split(" ")[1])
        channel_id = int(request.split(" ")[2]) if len(request.split(" ")) > 2 else None
        await dm_channel.send(f"Refreshing transaction: {record_id}")
        response = await client.refresh_transaction(
            record_id=record_id, channel_id=channel_id
        )
        await dm_channel.send(response)

    if request.startswith("shutdown"):
        log.info("Received shutdown command")
        parts = request.split(" ", 1)  # Split at most once
        received_auth_code = parts[1].upper() if len(parts) > 1 else None

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
            response = f"To shutdown {client.config["name"]}, please use the following command:\n"
            response += f"`!dev shutdown {auth_code}`\n"
            response += f"The code expires <t:{expiry}:R>\n"
            response += "\n"
            response += "⚠️⚠️⚠️"
            response += "\n"
            response += "This cannot be undone.\n"
            response += f"The only way to restart {client.config["name"]} is via a deployment.\n"
            response += "⚠️⚠️⚠️"
            response += "\n"

            await dm_channel.send(response)

        if received_auth_code == auth_code:
            log.info(f"Received valid shutdown code from {message.author.name}.")

            shutdown_time = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(minutes=5)
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
            response += f"Shutdown will commence at <t:{shutdown_ts}:t> (<t:{shutdown_ts}:R>).\n"
            response += "Use `!dev cancel_shutdown` to cancel."

            await dm_channel.send(response)

        else:
            log.info("Received invalid shutdown code.")

            response = "Invalid code. Please try again.\n"
            response += "\n"
            response += f"To shutdown {client.config["name"]}, please use the following command:\n"
            response += f"`!dev shutdown {auth_code}`\n"
            response += f"The code expires <t:{expiry}:R>\n"
            response += "\n"
            response += "⚠️⚠️⚠️"
            response += "\n"
            response += "This cannot be undone.\n"
            response += f"The only way to restart {client.config["name"]} is via a deployment.\n"
            response += "⚠️⚠️⚠️"
            response += "\n"

            await dm_channel.send(response)

    if request.startswith("cancel_shutdown"):
        job = client.scheduler.get_job("shutdown")
        if job:
            log.debug(f"Removing job {job}")
            job.remove()
            await dm_channel.send("Shutdown has been cancelled.")
