"""The entry point for ledger_bot."""

import logging
import logging.config
import os

from dotenv import load_dotenv

from .run_ledger_bot import start_bot

# Load environment variables from .env
load_dotenv()

# Set the log level based on the environment variable
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {log_level}")

# Configure logging
logging.config.fileConfig(fname="log.conf", disable_existing_loggers=False)
logging.getLogger().setLevel(numeric_level)
logging.getLogger("discord").setLevel(logging.ERROR)
logging.getLogger("discord.gateway").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("urllib").setLevel(logging.CRITICAL)
logging.getLogger("apscheduler.scheduler").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

if os.getenv("LOG_TO_FILE") == "false":
    logging.info("LOG_TO_FILE is false, removing FileHandlers")
    file_handlers = (
        handler
        for handler in logging.root.handlers
        if isinstance(handler, logging.FileHandler)
    )
    for handler in file_handlers:
        logging.root.removeHandler(handler)
elif os.getenv("LOG_FOLDER_PATH") is not None:
    logging.info(f"Updating logging FileHandler path to {os.getenv('LOG_FOLDER_PATH')}")

    file_handlers = (
        handler
        for handler in logging.root.handlers
        if isinstance(handler, logging.FileHandler)
    )
    for handler in file_handlers:
        handler.stream.close()
        handler.baseFilename = os.path.abspath(f"{os.getenv('LOG_FOLDER_PATH')}/log")
        handler.stream = handler._open()

log = logging.getLogger(__name__)

log.info("Starting ledger-bot")
start_bot()
