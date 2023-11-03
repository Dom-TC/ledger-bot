"""config.

module to process configs, defaults defined in the function, overwritten by provided data, and again by environment vars.
"""

import logging
import os

log = logging.getLogger(__name__)


def parse(config):
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
            "paid": "💸",
            "delivered": "🚚",
            "unknown_version": "🤷",
            "status_confirmed": "🟩",
            "status_part_confirmed": "🟨",
            "status_unconfirmed": "🟥",
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

    defaults["maintainer_ids"] = set(defaults["maintainer_ids"])
    log.info(f"Maintainer IDs: {defaults['maintainer_ids']}")

    return defaults
