"""DM command - dev."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.process_transactions import refresh_transaction
from ledger_bot.reactions import add_reaction
from ledger_bot.scheduled_commands import cleanup

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
        await cleanup(client=client, storage=client.transaction_storage)

    elif request.startswith("refresh_reminders"):
        await dm_channel.send("Refreshing reminders")
        await client.reminders.refresh_reminders()

    elif request.startswith("refresh_message"):
        row_id = int(request.split(" ")[1])
        channel_id = int(request.split(" ")[2]) if len(request.split(" ")) > 2 else None
        await dm_channel.send(f"Refreshing transaction: {row_id}")
        response = await refresh_transaction(
            client=client, row_id=row_id, channel_id=channel_id
        )
        await dm_channel.send(response)
