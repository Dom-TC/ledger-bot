"""run_ledger_bot.

This is the entry point for ledger_bot.
Ledger_bot is a Discord bot that allows users to track sales.

"""

import json
import logging
import logging.config
import os

from .config import parse
from .LedgerBot import LedgerBot
from .slash_commands import setup_slash
from .storage import AirtableStorage

log = logging.getLogger(__name__)


def run():
    """Run ledger-bot."""
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

    # Create client
    client = LedgerBot(config, storage)

    # Build slash commands
    setup_slash(client, config, storage)

    # Run bot
    client.run(config["authentication"]["discord"], log_handler=None)
