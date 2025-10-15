"""config.

module to process configs, defaults defined in the function, overwritten by provided data, and again by environment vars.
"""

import json
import logging
from dataclasses import dataclass, field, fields, is_dataclass
from os import getenv
from pathlib import Path
from typing import Any, Dict, List, get_args, get_origin

log = logging.getLogger(__name__)


@dataclass
class AuthenticationConfig:
    discord: str = ""
    airtable_key: str = ""
    airtable_base: str = ""

    def __repr__(self):
        fields = ", ".join(f"{f}='****'" for f in self.__dataclass_fields__)
        return f"<{self.__class__.__name__}({fields})>"


@dataclass
class ChannelsConfig:
    include: List = field(default_factory=list)
    exclude: List = field(default_factory=list)


@dataclass
class EmojiConfig:
    approval: str = "👍"
    cancel: str = "👎"
    paid: str = "💸"
    delivered: str = "🚚"
    reminder: str = "🔔"
    unknown_version: str = "🤷"
    thinking: str = "⏳"
    status_confirmed: str = "🟩"
    status_part_confirmed: str = "🟨"
    status_unconfirmed: str = "🟥"
    status_cancelled: str = "❌"


@dataclass
class RunCleanupTimeConfig:
    hour: str = "1"
    minute: str = "0"
    second: str = "0"


@dataclass
class ReminderRefreshTimeConfig:
    hour: str = "*/5"
    minute: str = "0"
    second: str = "0"


@dataclass
class ReactionRoleRefreshTimeConfig:
    hour: str = "*"
    minute: str = "*/30"
    second: str = "0"


@dataclass
class Config:
    bot_id: str = "Bot"
    name: str = "Ledger-Bot"
    guild: int = 0
    watching_status: str = "for empty glasses"
    delete_previous_bot_messages: bool = True
    cleanup_delay_hours: int = (
        24  # How many hours must have passed between a transaction being completed and it being cleaned
    )
    cleanup_removes_transaction_records: bool = False
    admin_role: int = 1184878800408948847
    database_path: Path = Path("data/ledger_bot.sql")
    shutdown_post_channel: int | None = None
    shutdown_delay: int = (
        5  # Time in minutes to wait after receiving a shutdown command
    )
    maintainer_ids: List[int] = field(
        default_factory=lambda: [
            760972696284299294,  # Dom_TC
            699641132497371162,  # .henry_1
            963548418385543188,  # OllyDS
            881831177311387689,  # chilloutbar
            127599224392122368,  # a5teenpoundz
        ]
    )

    authentication: AuthenticationConfig = field(default_factory=AuthenticationConfig)
    channels: ChannelsConfig = field(default_factory=ChannelsConfig)
    emojis: EmojiConfig = field(default_factory=EmojiConfig)
    run_cleanup_time: RunCleanupTimeConfig = field(default_factory=RunCleanupTimeConfig)
    reminder_refresh_time: ReminderRefreshTimeConfig = field(
        default_factory=ReminderRefreshTimeConfig
    )
    reaction_role_refresh_time: ReactionRoleRefreshTimeConfig = field(
        default_factory=ReactionRoleRefreshTimeConfig
    )

    @classmethod
    def load(cls, path: str | None = None) -> "Config":
        """Load configuration.

        Loads from multiple sources in the following levels of priority:
        1. Environment variables
        2. Config file (JSON)
        3. Defaults
        """
        # Start with defaults
        cfg = cls()

        # Load from file (YAML/JSON)
        file_path = Path(path or getenv("BOT_CONFIG", "config.json"))
        file_data: Dict[str, Any] = {}
        if file_path.is_file():
            log.info(f"Loading config from {file_path}")
            try:
                with open(file_path) as f:
                    file_data = json.load(f) or {}
            except (OSError, ValueError) as e:
                log.critical(f"Failed to parse config file {file_path}: {e}")
                exit(1)
        else:
            log.warning(f"Can't load config from {file_path}")

        # Apply file config
        cfg._apply_dict(cfg, file_data)

        # Apply environment overrides
        if token := getenv("BOT_DISCORD_TOKEN"):
            cfg.authentication.discord = token

        if token := getenv("BOT_AIRTABLE_KEY"):
            cfg.authentication.airtable_key = token

        if token := getenv("BOT_AIRTABLE_BASE"):
            cfg.authentication.airtable_base = token

        if token := getenv("DATABASE_URL"):
            cfg.database_path = Path(token)

        if token := getenv("BOT_ID"):
            cfg.bot_id = token

        log.info("Successfully loaded config")
        log.info(f"Maintainer IDs: {cfg.maintainer_ids}")

        log.debug(cfg)

        return cfg

    def _apply_dict(self, obj, data):
        for key, value in data.items():
            if hasattr(obj, key):
                current = getattr(obj, key)
                if is_dataclass(current) and isinstance(value, dict):
                    self._apply_dict(current, value)
                else:
                    field_type = next(
                        (f.type for f in fields(obj) if f.name == key), None
                    )
                    if field_type is Path:
                        setattr(obj, key, Path(value))
                    elif field_type is int:
                        setattr(obj, key, int(value))
                    elif field_type is bool:
                        if isinstance(value, str):
                            setattr(
                                obj, key, value.lower() in ("true", "1", "yes", "y")
                            )
                        else:
                            setattr(obj, key, bool(value))
                    elif get_origin(field_type) in (list, List):
                        args = get_args(type(current))
                        if args:
                            item_type = args[0]
                            setattr(obj, key, [item_type(v) for v in value])
                        else:
                            setattr(obj, key, list(value))
                    else:
                        setattr(obj, key, value)
