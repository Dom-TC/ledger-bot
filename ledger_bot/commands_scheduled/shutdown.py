"""shutdown.py."""

import asyncio
import logging
from typing import TYPE_CHECKING

from discord import DMChannel, TextChannel

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot


log = logging.getLogger(__name__)


async def shutdown(client: "LedgerBot", dm_channel: DMChannel) -> None:
    """
    Shutdown the bot.

    Parameters
    ----------
    client : LedgerBot
        The client
    """
    log.warning(f"Shutting down {client.config.name}...")

    log.debug("Posting shutdown message")

    if client.config.channels.shutdown_post_channel is not None:
        channel = await client.get_or_fetch_channel(
            client.config.channels.shutdown_post_channel
        )
    else:
        channel = None

    if channel is not None and isinstance(channel, TextChannel):
        await channel.send(
            f"<@{client.user.id if client.user else None}> is shutting down for scheduled maintanence.  Goodnight. 👋"
        )

    await dm_channel.send(
        f"<@{client.user.id if client.user else None}> is shutting down for scheduled maintanence.  Goodnight. 👋"
    )

    log.warning("Stopping scheduler")
    client.scheduler.shutdown()

    log.warning("Stopping database")

    log.warning("Stopping client")
    asyncio.get_event_loop().call_soon(asyncio.create_task, client.close())

    log.info("Bot successfully shutdown")
