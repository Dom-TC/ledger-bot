"""DM command - stats."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.message_generators import generate_stats_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def command_stats(
    client: "LedgerBot", message: discord.Message, dm_channel: discord.DMChannel
) -> None:
    """DM command - stats."""
    log.info(f"Getting stats for user {message.author.name} ({message.author.id})")

    stats_obj = await client.service.stats.get_stats(
        user=await client.service.member.get_or_add_member(message.author)
    )

    if stats_obj.server is None:
        await dm_channel.send("No transactions have been recorded.")

    else:
        response = generate_stats_message(stats=stats_obj)

        await dm_channel.send(response)
