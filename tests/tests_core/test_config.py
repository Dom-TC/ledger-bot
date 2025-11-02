"""Tests covering ledger_bot.core.config."""

import json
import logging
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from ledger_bot.core.config import (
    AuthenticationConfig,
    ChannelsConfig,
    Config,
    EmojiConfig,
    EventRegionConfig,
    JobSchedule,
)


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


def test_model_validate_simple_values():
    data = {
        "bot_id": "NewBot",
        "guild": 123,
        "delete_previous_bot_messages": False,
        "shutdown_delay": 10,
        "base_currency": "USD",
    }

    config = Config.model_validate(data)

    assert config.bot_id == "NewBot"
    assert config.guild == 123
    assert config.delete_previous_bot_messages is False
    assert config.shutdown_delay == 10
    assert config.base_currency == "USD"


def test_model_validate_nested_models():
    data = {
        "authentication": {
            "discord": "discord_token",
            "airtable_key": "airtable_key",
            "airtable_base": "airtable_base",
            "exchangerate_api": "exchange_api",
        },
        "run_cleanup_time": {"hour": 3, "minute": 15, "second": 30},
    }

    config = Config.model_validate(data)

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


def test_model_validate_path_field(tmp_path):
    file_path = tmp_path / "db.sqlite"
    file_path.touch()

    data = {"database_path": str(file_path)}

    config = Config.model_validate(data)

    assert config.database_path == file_path
    assert isinstance(config.database_path, Path)


def test_model_validate_timedelta_field():
    # Pydantic expects timedelta as total seconds or timedelta object
    td_value = timedelta(days=2, hours=5, minutes=30)
    data = {"currency_rate_update_delta": td_value}

    config = Config.model_validate(data)

    td = config.currency_rate_update_delta
    assert isinstance(td, timedelta)
    assert td.days == 2
    assert td.seconds == (5 * 3600 + 30 * 60)


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, True),
        (False, False),
        (0, False),
        (1, True),
    ],
)
def test_model_validate_bool_conversion(value, expected):
    data = {"delete_previous_bot_messages": value}

    config = Config.model_validate(data)

    assert config.delete_previous_bot_messages is expected


def test_model_validate_list_of_ints():
    data = {"maintainer_ids": [1, 2, 3]}

    config = Config.model_validate(data)

    assert config.maintainer_ids == [1, 2, 3]


def test_model_validate_unknown_field_is_ignored():
    data = {"not_a_field": "value", "bot_id": "CustomBot"}

    # Pydantic ignores unknown fields by default
    config = Config.model_validate(data)
    assert config.bot_id == "CustomBot"
    assert not hasattr(config, "not_a_field")


def test_model_validate_partial_nested_update():
    data = {"authentication": {"discord": "token_only"}}

    config = Config.model_validate(data)

    auth = config.authentication
    assert auth.discord == "token_only"
    # Other fields remain defaults
    assert auth.airtable_key == ""
    assert auth.airtable_base == ""
    assert auth.exchangerate_api == ""


# Tests for EventRegionConfig
def test_event_region_config_defaults():
    region = EventRegionConfig()

    assert region.region_name == ""
    assert region.new_event_category == 0
    assert region.event_post_channel == 0


def test_event_region_config_with_values():
    region = EventRegionConfig(
        region_name="Europe",
        new_event_category=123456,
        event_post_channel=789012,
    )

    assert region.region_name == "Europe"
    assert region.new_event_category == 123456
    assert region.event_post_channel == 789012


# Tests for ChannelsConfig
def test_channels_config_defaults():
    channels = ChannelsConfig()

    assert channels.include == []
    assert channels.exclude == []
    assert channels.event_regions == []
    assert channels.shutdown_post_channel is None


def test_channels_config_with_lists():
    channels = ChannelsConfig(
        include=[111, 222, 333],
        exclude=[444, 555],
        shutdown_post_channel=999,
    )

    assert channels.include == [111, 222, 333]
    assert channels.exclude == [444, 555]
    assert channels.shutdown_post_channel == 999


def test_channels_config_with_event_regions():
    data = {
        "event_regions": [
            {
                "region_name": "Europe",
                "new_event_category": 100,
                "event_post_channel": 200,
            },
            {
                "region_name": "Asia",
                "new_event_category": 300,
                "event_post_channel": 400,
            },
        ]
    }

    channels = ChannelsConfig.model_validate(data)

    assert len(channels.event_regions) == 2
    assert isinstance(channels.event_regions[0], EventRegionConfig)
    assert channels.event_regions[0].region_name == "Europe"
    assert channels.event_regions[0].new_event_category == 100
    assert channels.event_regions[1].region_name == "Asia"
    assert channels.event_regions[1].event_post_channel == 400


# Tests for EmojiConfig
def test_emoji_config_defaults():
    emojis = EmojiConfig()

    assert emojis.approval == "👍"
    assert emojis.cancel == "👎"
    assert emojis.paid == "💸"
    assert emojis.delivered == "🚚"
    assert emojis.reminder == "🔔"
    assert emojis.unknown_version == "🤷"
    assert emojis.thinking == "⏳"
    assert emojis.status_confirmed == "🟩"
    assert emojis.status_part_confirmed == "🟨"
    assert emojis.status_unconfirmed == "🟥"
    assert emojis.status_cancelled == "❌"


def test_emoji_config_custom_values():
    emojis = EmojiConfig(
        approval="✅",
        cancel="❌",
        paid="💰",
    )

    assert emojis.approval == "✅"
    assert emojis.cancel == "❌"
    assert emojis.paid == "💰"
    # Others remain defaults
    assert emojis.delivered == "🚚"


# Tests for JobSchedule with string values
def test_job_schedule_with_string_values():
    schedule = JobSchedule(hour="*/5", minute="*/30", second="0")

    assert schedule.hour == "*/5"
    assert schedule.minute == "*/30"
    assert schedule.second == "0"


def test_job_schedule_mixed_string_and_int():
    schedule = JobSchedule(hour="*", minute=15, second=0)

    assert schedule.hour == "*"
    assert schedule.minute == 15
    assert schedule.second == 0


def test_job_schedule_defaults():
    schedule = JobSchedule()

    assert schedule.hour == "*"
    assert schedule.minute == 0
    assert schedule.second == 0


# Tests for environment variable priority
def test_env_overrides_config_file(tmp_path, monkeypatch):
    """Test that environment variables override config file values."""
    monkeypatch.chdir(tmp_path)

    temp_file = tmp_path / "config.json"
    config_data = {
        "bot_id": "FileBot",
        "authentication": {
            "discord": "file_token",
            "airtable_key": "file_key",
        },
        "database_path": "file_db.sql",
    }
    temp_file.write_text(json.dumps(config_data))

    # Set env vars that should override file values
    monkeypatch.setenv("BOT_ID", "EnvBot")
    monkeypatch.setenv("BOT_DISCORD_TOKEN", "env_token")
    monkeypatch.setenv("DATABASE_URL", "env_db.sql")

    config = Config.load(temp_file)

    # Env vars should win
    assert config.bot_id == "EnvBot"
    assert config.authentication.discord == "env_token"
    assert config.database_path == Path("env_db.sql")
    # File value should remain for non-overridden fields
    assert config.authentication.airtable_key == "file_key"


def test_partial_env_override(tmp_path, monkeypatch):
    """Test that only set env vars override, others use file/defaults."""
    monkeypatch.chdir(tmp_path)

    temp_file = tmp_path / "config.json"
    config_data = {
        "authentication": {
            "discord": "file_discord",
            "airtable_key": "file_airtable",
        }
    }
    temp_file.write_text(json.dumps(config_data))

    # Only override discord
    monkeypatch.setenv("BOT_DISCORD_TOKEN", "env_discord")

    config = Config.load(temp_file)

    assert config.authentication.discord == "env_discord"
    assert config.authentication.airtable_key == "file_airtable"
    # Non-file, non-env fields remain defaults
    assert config.authentication.airtable_base == ""


# Tests for default factory initialization
def test_maintainer_ids_default_factory():
    """Test that default maintainer IDs are properly initialized."""
    config1 = Config()
    config2 = Config()

    # Should have default IDs
    assert len(config1.maintainer_ids) == 5
    assert 760972696284299294 in config1.maintainer_ids

    # Each instance should have its own list (not shared)
    config1.maintainer_ids.append(999)
    assert 999 in config1.maintainer_ids
    assert 999 not in config2.maintainer_ids


def test_channels_default_factory():
    """Test that ChannelsConfig uses default factory correctly."""
    config1 = Config()
    config2 = Config()

    # Should have empty lists by default
    assert config1.channels.include == []
    assert config1.channels.exclude == []

    # Each instance should have its own lists
    config1.channels.include.append(123)
    assert 123 in config1.channels.include
    assert 123 not in config2.channels.include


def test_job_schedule_default_factories():
    """Test that JobSchedule fields use correct default factories."""
    config = Config()

    # run_cleanup_time should have specific defaults
    assert config.run_cleanup_time.hour == 1
    assert config.run_cleanup_time.minute == 0
    assert config.run_cleanup_time.second == 0

    # reminder_refresh_time should have cron-style defaults
    assert config.reminder_refresh_time.hour == "*/5"
    assert config.reminder_refresh_time.minute == 0

    # reaction_role_refresh_time
    assert config.reaction_role_refresh_time.hour == "*"
    assert config.reaction_role_refresh_time.minute == "*/30"


# Tests for config serialization
def test_config_model_dump():
    """Test that config can be serialized to dict."""
    config = Config(
        bot_id="TestBot",
        guild=12345,
        base_currency="USD",
    )

    data = config.model_dump()

    assert isinstance(data, dict)
    assert data["bot_id"] == "TestBot"
    assert data["guild"] == 12345
    assert data["base_currency"] == "USD"
    assert "authentication" in data
    assert isinstance(data["authentication"], dict)


def test_config_model_dump_json():
    """Test that config can be serialized to JSON."""
    config = Config(
        bot_id="TestBot",
        name="Test",
    )

    json_str = config.model_dump_json()

    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["bot_id"] == "TestBot"
    assert data["name"] == "Test"


def test_config_roundtrip_serialization():
    """Test that config can be serialized and deserialized."""
    original = Config(
        bot_id="RoundtripBot",
        guild=99999,
        maintainer_ids=[1, 2, 3],
    )

    # Serialize to JSON
    json_str = original.model_dump_json()

    # Deserialize back
    restored = Config.model_validate_json(json_str)

    assert restored.bot_id == original.bot_id
    assert restored.guild == original.guild
    assert restored.maintainer_ids == [1, 2, 3]


# Tests for type validation errors
def test_invalid_type_for_guild():
    """Test that invalid type for guild field raises ValidationError."""
    data = {"guild": "not_an_int"}

    with pytest.raises(ValidationError) as exc_info:
        Config.model_validate(data)

    assert "guild" in str(exc_info.value)


def test_invalid_type_for_bool_field():
    """Test that invalid type for bool field raises ValidationError."""
    data = {"delete_previous_bot_messages": "not_a_bool"}

    with pytest.raises(ValidationError) as exc_info:
        Config.model_validate(data)

    assert "delete_previous_bot_messages" in str(exc_info.value)


def test_invalid_type_for_list_field():
    """Test that invalid type for list field raises ValidationError."""
    data = {"maintainer_ids": "not_a_list"}

    with pytest.raises(ValidationError) as exc_info:
        Config.model_validate(data)

    assert "maintainer_ids" in str(exc_info.value)


def test_invalid_type_in_list_elements():
    """Test that invalid types in list elements raise ValidationError."""
    data = {"maintainer_ids": [1, 2, "not_an_int", 4]}

    with pytest.raises(ValidationError) as exc_info:
        Config.model_validate(data)

    assert "maintainer_ids" in str(exc_info.value)


def test_invalid_nested_config():
    """Test that invalid nested config raises ValidationError."""
    data = {
        "authentication": {
            "discord": 12345,  # Should be string, not int
        }
    }

    with pytest.raises(ValidationError) as exc_info:
        Config.model_validate(data)

    assert "discord" in str(exc_info.value)


def test_invalid_event_region_in_channels():
    """Test that invalid EventRegionConfig raises ValidationError."""
    data = {
        "channels": {
            "event_regions": [
                {
                    "region_name": "Valid",
                    "new_event_category": "not_an_int",  # Should be int
                }
            ]
        }
    }

    with pytest.raises(ValidationError) as exc_info:
        Config.model_validate(data)

    assert "new_event_category" in str(exc_info.value)
