"""Tests for ledger_bot/config.py."""

import os
from typing import Dict

import pytest

from ledger_bot import config


@pytest.fixture()
def mock_os_getenv(monkeypatch):
    monkeypatch.setattr(os, "getenv", lambda x: None)


@pytest.fixture
def default_config():
    return {
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
        "reaction_role_refresh_time": {
            "hour": "*",
            "minute": "*/30",
            "second": "0",
        },
        "cleanup_removes_transaction_records": False,
    }


def test_parse_with_provided_none(default_config, mock_os_getenv):
    provided_config = None
    parsed_config = config.parse(provided_config)
    assert parsed_config == default_config


def test_parse_with_provided_empty(default_config, mock_os_getenv):
    provided_config = {}
    parsed_config = config.parse(provided_config)
    assert parsed_config == default_config


def test_parse_with_provided_input(default_config, mock_os_getenv):
    provided_config = {
        "name": "TrackerBot",
        "channels": {"include": ["testing"]},
        "guild": 1167144773090558034,
    }

    parsed_config = config.parse(provided_config)

    assert parsed_config["name"] == provided_config["name"]
    assert (
        parsed_config["channels"]["include"] == provided_config["channels"]["include"]
    )
    assert parsed_config["guild"] == provided_config["guild"]

    assert (
        parsed_config["delete_previous_bot_messages"]
        == default_config["delete_previous_bot_messages"]
    )
    assert parsed_config["emojis"] == default_config["emojis"]
    assert parsed_config["cleanup_delay_hours"] == default_config["cleanup_delay_hours"]


def test_parse_with_extra_input(default_config, mock_os_getenv):
    provided_config = {"invalid_key": True}

    parsed_config = config.parse(provided_config)

    assert parsed_config == default_config


def test_parse_config_with_env_var_override(monkeypatch):
    monkeypatch.setenv("BOT_ID", "env_bot_id")
    monkeypatch.setenv("BOT_DISCORD_TOKEN", "env_discord_token")
    monkeypatch.setenv("BOT_AIRTABLE_KEY", "env_airtable_key")
    monkeypatch.setenv("BOT_AIRTABLE_BASE", "env_airtable_base")

    parsed_config = config.parse({})
    assert parsed_config["id"] == "env_bot_id"
    assert parsed_config["authentication"]["discord"] == "env_discord_token"
    assert parsed_config["authentication"]["airtable_key"] == "env_airtable_key"
    assert parsed_config["authentication"]["airtable_base"] == "env_airtable_base"
