"""config.

module to process configs, defaults defined in the function, overwritten by provided data, and again by environment vars.
"""

import logging
from datetime import timedelta
from os import getenv
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class AuthenticationConfig(BaseModel):
    discord: str = ""
    airtable_key: str = ""
    airtable_base: str = ""
    exchangerate_api: str = ""

    def __repr__(self):
        fields = ", ".join(f"{f}='****'" for f in self.model_fields)
        return f"<{self.__class__.__name__}({fields})>"


class EventRegionConfig(BaseModel):
    region_name: str = ""
    new_event_category: int = 0
    event_post_channel: int = 0


class ChannelsConfig(BaseModel):
    include: List = Field(default_factory=list)
    exclude: List = Field(default_factory=list)
    event_regions: List[EventRegionConfig] = Field(default_factory=list)
    shutdown_post_channel: int | None = None


class EmojiConfig(BaseModel):
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


class JobSchedule(BaseModel):
    hour: str | int = "*"
    minute: str | int = 0
    second: str | int = 0


class Config(BaseModel):
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
    shutdown_delay: int = (
        5  # Time in minutes to wait after receiving a shutdown command
    )
    maintainer_ids: List[int] = Field(
        default_factory=lambda: [
            760972696284299294,  # Dom_TC
            699641132497371162,  # .henry_1
            963548418385543188,  # OllyDS
            881831177311387689,  # chilloutbar
            127599224392122368,  # a5teenpoundz
        ]
    )

    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    emojis: EmojiConfig = Field(default_factory=EmojiConfig)
    run_cleanup_time: JobSchedule = Field(
        default_factory=lambda: JobSchedule(hour=1, minute=0, second=0)
    )
    reminder_refresh_time: JobSchedule = Field(
        default_factory=lambda: JobSchedule(hour="*/5", minute=0, second=0)
    )
    reaction_role_refresh_time: JobSchedule = Field(
        default_factory=lambda: JobSchedule(hour="*", minute="*/30", second=0)
    )
    base_currency: str = "GBP"
    currency_rate_update_delta: timedelta = timedelta(days=1)
    id_offset: int = 0

    @classmethod
    def load(cls, path: str | None = None) -> "Config":
        """Load configuration.

        Loads from multiple sources in the following levels of priority:
        1. Environment variables
        2. Config file (JSON)
        3. Defaults
        """
        # Load from file (JSON)
        file_path = Path(path if path else getenv("BOT_CONFIG", "config.json"))

        if file_path.is_file():
            log.info(f"Loading config from {file_path}")
            try:
                with open(file_path) as f:
                    cfg = cls.model_validate_json(f.read())
            except (OSError, ValueError) as e:
                log.critical(f"Failed to parse config file {file_path}: {e}")
                exit(1)
        else:
            log.warning(f"Can't load config from {file_path}")
            # Start with defaults
            cfg = cls()

        # Apply environment overrides
        if token := getenv("BOT_DISCORD_TOKEN"):
            cfg.authentication.discord = token

        if token := getenv("BOT_AIRTABLE_KEY"):
            cfg.authentication.airtable_key = token

        if token := getenv("BOT_AIRTABLE_BASE"):
            cfg.authentication.airtable_base = token

        if token := getenv("EXCHANGERATE_API"):
            cfg.authentication.exchangerate_api = token

        if token := getenv("DATABASE_URL"):
            cfg.database_path = Path(token)

        if token := getenv("BOT_ID"):
            cfg.bot_id = token

        log.info("Successfully loaded config")
        log.info(f"Maintainer IDs: {cfg.maintainer_ids}")

        log.debug(cfg)

        return cfg
