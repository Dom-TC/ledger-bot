"""config.

module to process configs, defaults defined in the function, overwritten by provided data, and again by environment vars.
"""

import logging
import os
from datetime import datetime

log = logging.getLogger(__name__)


def parse(config: dict) -> dict:
    """
    Parse provided config, with defaults and env vars.

    Returns dict
    """
    defaults = {
        "id": None,
        "name": "Ledger-Bot",
        "authentication": {
            "discord": "",
            "airtable_key": "",
            "airtable_base": "",
        },
        "channels": {
            "include": [],
            "exclude": [],
        },
        "triggers": {
            "new_transaction": [],
        },
        "emojis": {
            "approval": "👍",
            "cancel": "👎",
            "paid": "💸",
            "delivered": "🚚",
            "reminder": "🔔",
            "unknown_version": "🤷",
            "thinking": "⏳",
            "status_confirmed": "🟩",
            "status_part_confirmed": "🟨",
            "status_unconfirmed": "🟥",
            "status_cancelled": "❌",
        },
        "guild": None,
        "watching_status": "for empty glasses",
        "delete_previous_bot_messages": True,
        "maintainer_ids": [
            760972696284299294,  # Dom_TC
            699641132497371162,  # .henry_1
            963548418385543188,  # OllyDS
            881831177311387689,  # chilloutbar
        ],
        "cleanup_delay_hours": 24,  # How many hours must have passed between a transaction being completed and it being cleaned
        "run_cleanup_time": {
            "hour": 1,
            "minute": "0",
            "second": "0",
        },
        "reminder_refresh_time": {
            "hour": "*/5",
            "minute": "0",
            "second": "0",
        },
        "cleanup_removes_transaction_records": False,
    }

    # Update defaults from config file
    for key in defaults.keys():
        if isinstance(defaults[key], dict):
            defaults[key].update(config.get(key, {}))
        else:
            defaults[key] = config.get(key, defaults[key])

    # Environment variables override config files
    if token := os.getenv("BOT_DISCORD_TOKEN"):
        defaults["authentication"]["discord"] = token

    if token := os.getenv("BOT_AIRTABLE_KEY"):
        defaults["authentication"]["airtable_key"] = token

    if token := os.getenv("BOT_AIRTABLE_BASE"):
        defaults["authentication"]["airtable_base"] = token

    if bot_id := os.getenv("BOT_ID"):
        defaults["id"] = bot_id

    log.info(f"Maintainer IDs: {defaults['maintainer_ids']}")

    return defaults
