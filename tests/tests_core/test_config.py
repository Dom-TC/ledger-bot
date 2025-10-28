"""Tests covering ledger_bot.core.config."""

import logging
from datetime import timedelta
from pathlib import Path

import pytest

from ledger_bot.core.config import AuthenticationConfig, Config, JobSchedule


@pytest.fixture(autouse=True)
def no_env(monkeypatch):
    monkeypatch.delenv("BOT_CONFIG", raising=False)
    monkeypatch.delenv("BOT_DISCORD_TOKEN", raising=False)
    monkeypatch.delenv("BOT_AIRTABLE_KEY", raising=False)
    monkeypatch.delenv("BOT_AIRTABLE_BASE", raising=False)
    monkeypatch.delenv("EXCHANGERATE_API", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("BOT_ID", raising=False)


def test_config_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    config = Config.load()

    assert isinstance(config, Config)
    assert config.name == "Ledger-Bot"
    assert config.bot_id == "Bot"
    assert isinstance(config.authentication, AuthenticationConfig)
    assert config.authentication.discord == ""
    assert config.authentication.exchangerate_api == ""


def test_config_load_from_json_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    temp_dir = tmp_path / "config"
    temp_dir.mkdir()

    temp_file = temp_dir / "config.json"

    temp_file.write_text('{"name": "Pytest"}')

    config = Config.load(temp_file)

    assert isinstance(config, Config)
    assert config.name == "Pytest"
    assert config.bot_id == "Bot"
    assert isinstance(config.authentication, AuthenticationConfig)
    assert config.authentication.discord == ""
    assert config.authentication.exchangerate_api == ""


def test_config_load_from_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    temp_dir = tmp_path / "config"
    temp_dir.mkdir()

    temp_file = temp_dir / "envconfig.json"

    temp_file.write_text('{"bot_id": "NotThisOne"}')

    monkeypatch.setenv("BOT_CONFIG", f"{temp_file}")
    monkeypatch.setenv("BOT_DISCORD_TOKEN", "bot_discord_token")
    monkeypatch.setenv("BOT_AIRTABLE_KEY", "bot_airtable_key")
    monkeypatch.setenv("BOT_AIRTABLE_BASE", "bot_airtable_base")
    monkeypatch.setenv("EXCHANGERATE_API", "exchange_api")
    monkeypatch.setenv("DATABASE_URL", "db_url")
    monkeypatch.setenv("BOT_ID", "TestID")

    config = Config.load()

    assert isinstance(config, Config)
    assert config.bot_id == "TestID"
    assert config.authentication.discord == "bot_discord_token"
    assert config.authentication.airtable_key == "bot_airtable_key"
    assert config.authentication.airtable_base == "bot_airtable_base"
    assert config.authentication.exchangerate_api == "exchange_api"
    assert config.database_path == Path("db_url")
    assert isinstance(config.authentication, AuthenticationConfig)


def test_config_load_missing_file(tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)

    with caplog.at_level(logging.WARNING):
        config = Config.load("missing.json")

    assert "Can't load config from missing.json" in caplog.text
    assert isinstance(config, Config)


def test_config_load_invalid_json(tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)

    temp_dir = tmp_path / "config"
    temp_dir.mkdir()

    temp_file = temp_dir / "config.json"

    temp_file.write_text("THIS ISNT JSON")

    with pytest.raises(SystemExit) as excinfo:
        with caplog.at_level(logging.CRITICAL):
            config = Config.load(temp_file)

    assert f"Failed to parse config file {temp_file}" in caplog.text
    assert excinfo.value.code == 1


def test_authentication_config_repr():
    auth_config = AuthenticationConfig(
        discord="discord_secret",
        airtable_key="airtable_key_secret",
        airtable_base="airtable_base_secret",
        exchangerate_api="exchangerate_api_secret",
    )

    repr_str = repr(auth_config)

    assert "discord_secret" not in repr_str
    assert "airtable_key_secret" not in repr_str
    assert "airtable_base_secret" not in repr_str
    assert "exchangerate_api_secret" not in repr_str
    assert "****" in repr_str


def test_apply_dict_simple_values():
    data = {
        "bot_id": "NewBot",
        "guild": "123",  # str that should become int
        "delete_previous_bot_messages": "false",  # str -> bool
        "shutdown_delay": 10,
        "base_currency": "USD",
    }

    config = Config()
    config._apply_dict(config, data)

    assert config.bot_id == "NewBot"
    assert config.guild == 123
    assert config.delete_previous_bot_messages is False
    assert config.shutdown_delay == 10
    assert config.base_currency == "USD"


def test_apply_dict_nested_dataclass():
    data = {
        "authentication": {
            "discord": "discord_token",
            "airtable_key": "airtable_key",
            "airtable_base": "airtable_base",
            "exchangerate_api": "exchange_api",
        },
        "run_cleanup_time": {"hour": 3, "minute": 15, "second": 30},
    }

    config = Config()
    config._apply_dict(config, data)

    auth = config.authentication
    assert isinstance(auth, AuthenticationConfig)
    assert auth.discord == "discord_token"
    assert auth.airtable_key == "airtable_key"
    assert auth.airtable_base == "airtable_base"
    assert auth.exchangerate_api == "exchange_api"

    schedule = config.run_cleanup_time
    assert isinstance(schedule, JobSchedule)
    assert schedule.hour == 3
    assert schedule.minute == 15
    assert schedule.second == 30


def test_apply_dict_path_field(tmp_path):
    file_path = tmp_path / "db.sqlite"
    file_path.touch()

    data = {"database_path": str(file_path)}

    config = Config()
    config._apply_dict(config, data)

    assert config.database_path == file_path
    assert isinstance(config.database_path, Path)


def test_apply_dict_timedelta_field():
    data = {"currency_rate_update_delta": {"days": 2, "hours": 5, "minutes": 30}}

    config = Config()
    config._apply_dict(config, data)

    td = config.currency_rate_update_delta
    assert isinstance(td, timedelta)
    assert td.days == 2
    assert td.seconds == (5 * 3600 + 30 * 60)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("1", True),
        ("yes", True),
        ("y", True),
        ("false", False),
        ("0", False),
        (0, False),
        (1, True),
    ],
)
def test_apply_dict_bool_conversion(value, expected):
    data = {"delete_previous_bot_messages": value}

    config = Config()
    config._apply_dict(config, data)

    assert config.delete_previous_bot_messages is expected


def test_apply_dict_list_of_ints():
    data = {"maintainer_ids": [1, 2, 3]}

    config = Config()
    config._apply_dict(config, data)

    assert config.maintainer_ids == [1, 2, 3]


def test_apply_dict_unknown_field_is_ignored():
    data = {"not_a_field": "value"}

    config = Config()
    # Should not raise, and config remains unchanged for existing fields
    config._apply_dict(config, data)
    assert getattr(config, "bot_id") == "Bot"


def test_apply_dict_partial_nested_update():
    data = {"authentication": {"discord": "token_only"}}

    config = Config()
    config._apply_dict(config, data)

    auth = config.authentication
    assert auth.discord == "token_only"
    # Other fields remain defaults
    assert auth.airtable_key == ""
    assert auth.airtable_base == ""
    assert auth.exchangerate_api == ""
