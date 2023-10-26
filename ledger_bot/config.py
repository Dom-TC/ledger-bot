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
        "watching_status": "for empty glasses",
        "maintainer_ids": [],
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
