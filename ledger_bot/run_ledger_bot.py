"""run_ledger_bot.

Ledger_bot is a Discord bot that allows users to track sales.

"""

import asyncio
import json
import logging
import os
from asyncio.events import AbstractEventLoop
from datetime import timezone, tzinfo
from functools import partial
from signal import SIGINT, SIGTERM, Signals
from sys import platform
from typing import Any, Dict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .commands_slash import setup_slash
from .config import parse
from .database import setup_database
from .errors import SignalHaltError
from .LedgerBot import LedgerBot
from .reminder_manager import ReminderManager
from .services import (
    BotMessageService,
    MemberService,
    ReactionRoleService,
    ReminderService,
    Service,
    TransactionService,
)
from .storage import (
    BotMessageStorage,
    MemberStorage,
    ReactionRoleStorage,
    ReminderStorage,
    Storage,
    TransactionStorage,
)

log = logging.getLogger(__name__)


async def _run_bot(client: LedgerBot, config: Dict[str, Any]) -> None:
    """Run ledger-bot."""
    async with client:
        await client.start(config["authentication"]["discord"])


def _stop_bot(signal_enum: Signals, loop: AbstractEventLoop) -> None:
    """Stop the bot loop on KeyboardInterupt."""
    log.warning(f"Received signal {signal_enum} - Exiting...")
    loop.stop()
    raise SignalHaltError(signal_enum=signal_enum)


def start_bot() -> None:
    """Start ledger-bot."""
    # Get configs
    try:
        config_path = os.getenv("BOT_CONFIG", "config.json")
        log.debug(f"Config path: {config_path}")
        config_to_parse = {}
        if os.path.isfile(config_path):
            with open(config_path) as config_file:
                config_to_parse = json.load(config_file)
        config = parse(config_to_parse)
    except (OSError, ValueError) as err:
        log.error(f"Config file invalid: {err}")
        exit(1)

    # Setup databse
    db_session_factory = setup_database(config=config)

    # Create storage
    log.info("Setting up storage")
    storage = Storage(
        member=MemberStorage(db_session_factory),
        transaction=TransactionStorage(db_session_factory),
        bot_message=BotMessageStorage(db_session_factory),
        reminder=ReminderStorage(db_session_factory),
        reaction_role=ReactionRoleStorage(db_session_factory),
    )

    # Create services
    log.info("Setting up services")
    service = Service(
        member=MemberService(storage.member, config["bot_name"]),
        transaction=TransactionService(storage.transaction, config["bot_name"]),
        bot_message=BotMessageService(storage.bot_message, config["bot_name"]),
        reminder=ReminderService(storage.reminder, config["bot_name"]),
        reaction_role=ReactionRoleService(storage.reaction_role, config["bot_name"]),
    )

    # Create scheduler
    # Try to use IANA timezone first, fallback to UTC if missing
    try:
        tz: tzinfo = ZoneInfo("UTC")
    except ZoneInfoNotFoundError:
        tz = timezone.utc
    scheduler = AsyncIOScheduler(timezone=tz)

    # Create reminder_manager
    reminder_manager = ReminderManager(
        config=config, scheduler=scheduler, service=service
    )

    # Create client
    client = LedgerBot(
        config=config,
        service=service,
        scheduler=scheduler,
        reminders=reminder_manager,
    )

    # Pass client back into reminder manager.
    reminder_manager.set_client(client)

    # Build slash commands
    setup_slash(
        client=client,
    )

    # Run bot
    loop = asyncio.get_event_loop()

    # Handle keyboard interrupts
    for signal_enum in [SIGINT, SIGTERM]:
        exit_func = partial(_stop_bot, signal_enum=signal_enum, loop=loop)

        # add_signal_hander() only works on UNIX platforms.  Therefore check if not windows before adding it.
        if platform != "win32" and platform != "cygwin":
            loop.add_signal_handler(signal_enum, exit_func)

    try:
        loop.run_until_complete(_run_bot(client=client, config=config))
    except SignalHaltError:
        pass
    else:
        raise
