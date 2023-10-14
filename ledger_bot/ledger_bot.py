"""ledger_bot.

ledger_bot is a Discord bot that allows users to track sales.

"""

import logging
import logging.config
import os

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.config.fileConfig(fname="log.conf", disable_existing_loggers=False)
logging.getLogger("discord").setLevel(logging.CRITICAL)
logging.getLogger("discord.gateway").setLevel(logging.INFO)
if os.getenv("LOG_TO_FILE") == "false":
    logging.info("LOG_TO_FILE is false, removing FileHandlers")
    file_handlers = (
        handler
        for handler in logging.root.handlers
        if isinstance(handler, logging.FileHandler)
    )
    for handler in file_handlers:
        logging.root.removeHandler(handler)
log = logging.getLogger("ledger_bot")
