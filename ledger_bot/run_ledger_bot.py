"""run_ledger_bot.

This is the entry point for ledger_bot.
Ledger_bot is a Discord bot that allows users to track sales.

"""

import json
import logging
import logging.config
import os

from config import parse
from dotenv import load_dotenv
from LedgerBot import LedgerBot
from storage import AirtableStorage

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.config.fileConfig(fname="log.conf", disable_existing_loggers=False)
logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.getLogger("discord.gateway").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("urllib").setLevel(logging.CRITICAL)
if os.getenv("LOG_TO_FILE") == "false":
    logging.info("LOG_TO_FILE is false, removing FileHandlers")
    file_handlers = (
        handler
        for handler in logging.root.handlers
        if isinstance(handler, logging.FileHandler)
    )
    for handler in file_handlers:
        logging.root.removeHandler(handler)
log = logging.getLogger(__name__)

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

storage = AirtableStorage(
    config["authentication"]["airtable_base"],
    config["authentication"]["airtable_key"],
    config["id"],
)

client = LedgerBot(config, storage)
client.run(config["authentication"]["discord"], log_handler=None)
