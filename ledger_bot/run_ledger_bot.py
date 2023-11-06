"""run_ledger_bot.

Ledger_bot is a Discord bot that allows users to track sales.

"""

import asyncio
import json
import logging
import logging.config
import os
from asyncio.events import AbstractEventLoop
from functools import partial
from signal import SIGINT, SIGTERM, Signals

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import parse
from .errors import SignalHaltError
from .LedgerBot import LedgerBot
from .slash_commands import setup_slash
from .storage import AirtableStorage

log = logging.getLogger(__name__)


async def _run_bot(client: LedgerBot, config: dict):
    """Run ledger-bot."""
    async with client:
        await client.start(config["authentication"]["discord"])


def _stop_bot(signal_enum: Signals, loop: AbstractEventLoop) -> None:
    """Stop the bot loop on KeyboardInterupt."""
    log.warning(f"Received signal {signal_enum} - Exiting...")
    loop.stop()
    raise SignalHaltError(signal_enum=signal_enum)


def start_bot():
    """Start ledger-bot."""
    # Get configs
    try:
        config_path = os.getenv("BOT_CONFIG", "config.json")
        log.debug(f"Config path: {config_path}")
        config_to_parse = {}
        if os.path.isfile(config_path):
            with open(config_path, mode="r") as config_file:
                config_to_parse = json.load(config_file)
        config = parse(config_to_parse)
    except (OSError, ValueError) as err:
        log.error(f"Config file invalid: {err}")
        exit(1)

    # Create storage
    storage = AirtableStorage(
        config["authentication"]["airtable_base"],
        config["authentication"]["airtable_key"],
        config["id"],
    )

    # Create scheduler
    scheduler = AsyncIOScheduler(timezone="utc")

    # Create client
    client = LedgerBot(config=config, storage=storage, scheduler=scheduler)

    # Build slash commands
    setup_slash(client, config, storage)

    # Run bot
    loop = asyncio.get_event_loop()

    # Handle keyboard interrupts
    for signal_enum in [SIGINT, SIGTERM]:
        exit_func = partial(_stop_bot, signal_enum=signal_enum, loop=loop)
        loop.add_signal_handler(signal_enum, exit_func)

    try:
        loop.run_until_complete(_run_bot(client=client, config=config))
    except SignalHaltError:
        pass
    else:
        raise
