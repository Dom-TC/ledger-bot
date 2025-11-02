"""Tests for run_ledger_bot module."""

from signal import SIGINT, SIGTERM
from unittest.mock import AsyncMock, Mock, patch

import pytest


def _close_coroutine(coro):
    """Close a coroutine to prevent 'coroutine was never awaited' warnings.

    This helper is used in tests that mock run_until_complete to ensure
    coroutines are properly closed instead of being left dangling.
    """
    try:
        coro.close()
    except (AttributeError, StopIteration):
        pass
    return None


@pytest.mark.asyncio
async def test_run_bot(mock_config):
    """Test _run_bot function."""
    from ledger_bot.run_ledger_bot import _run_bot

    mock_client = Mock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.start = AsyncMock()

    await _run_bot(mock_client, mock_config)

    mock_client.start.assert_called_once_with("test_token")


def test_stop_bot():
    """Test _stop_bot function."""
    from ledger_bot.errors import SignalHaltError
    from ledger_bot.run_ledger_bot import _stop_bot

    mock_loop = Mock()
    mock_loop.stop = Mock()

    with pytest.raises(SignalHaltError):
        _stop_bot(SIGINT, mock_loop)

    mock_loop.stop.assert_called_once()


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.LedgerBot")
@patch("ledger_bot.run_ledger_bot.setup_slash")
@patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot(
    mock_reminder_manager,
    mock_get_event_loop,
    mock_setup_slash,
    mock_ledger_bot_class,
    mock_setup_database,
    mock_config_class,
    mock_config,
):
    """Test start_bot function initialization."""
    from ledger_bot.run_ledger_bot import start_bot

    # Use the real mock_config fixture
    mock_config_class.load = Mock(return_value=mock_config)

    # Mock database setup
    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock LedgerBot
    mock_client = Mock()
    mock_ledger_bot_class.return_value = mock_client

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    # Mock event loop
    mock_loop = Mock()
    mock_loop.add_signal_handler = Mock()
    mock_loop.run_until_complete = Mock()
    mock_get_event_loop.return_value = mock_loop

    # Run start_bot
    start_bot()

    # Verify config was loaded
    mock_config_class.load.assert_called_once()

    # Verify database was setup
    mock_setup_database.assert_called_once_with(config=mock_config)

    # Verify LedgerBot was created
    mock_ledger_bot_class.assert_called_once()

    # Verify slash commands were setup
    mock_setup_slash.assert_called_once()

    # Verify loop ran
    mock_loop.run_until_complete.assert_called_once()


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.Storage")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_creates_storage(
    mock_reminder_manager,
    mock_storage_class,
    mock_setup_database,
    mock_config_class,
    mock_config,
):
    """Test that start_bot creates storage instances."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot"):
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete = Mock(
                    side_effect=_close_coroutine
                )

                start_bot()

    # Verify Storage was instantiated
    mock_storage_class.assert_called_once()


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.Service")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_creates_services(
    mock_reminder_manager,
    mock_service_class,
    mock_setup_database,
    mock_config_class,
    mock_config,
):
    """Test that start_bot creates service instances."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot"):
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete = Mock(
                    side_effect=_close_coroutine
                )

                start_bot()

    # Verify Service was instantiated
    mock_service_class.assert_called_once()


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.AsyncIOScheduler")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_creates_scheduler(
    mock_reminder_manager,
    mock_scheduler_class,
    mock_setup_database,
    mock_config_class,
    mock_config,
):
    """Test that start_bot creates a scheduler."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot"):
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete = Mock(
                    side_effect=_close_coroutine
                )

                start_bot()

    # Verify scheduler was created
    mock_scheduler_class.assert_called_once()


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_creates_reminder_manager(
    mock_reminder_manager_class, mock_setup_database, mock_config_class, mock_config
):
    """Test that start_bot creates a reminder manager."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    mock_reminder_manager = Mock()
    mock_reminder_manager.set_client = Mock()
    mock_reminder_manager_class.return_value = mock_reminder_manager

    with patch("ledger_bot.run_ledger_bot.LedgerBot"):
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete = Mock(
                    side_effect=_close_coroutine
                )

                start_bot()

    # Verify reminder manager was created
    mock_reminder_manager_class.assert_called_once()
    # Verify client was set on reminder manager
    mock_reminder_manager.set_client.assert_called_once()


@patch("ledger_bot.run_ledger_bot.platform", "win32")
@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_windows_no_signal_handlers(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that signal handlers are not added on Windows."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot"):
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_event_loop = Mock()
                mock_event_loop.add_signal_handler = Mock()
                mock_event_loop.run_until_complete = Mock(side_effect=_close_coroutine)
                mock_loop.return_value = mock_event_loop

                start_bot()

                # On Windows, signal handlers should not be added
                mock_event_loop.add_signal_handler.assert_not_called()


@patch("ledger_bot.run_ledger_bot.ZoneInfo")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_scheduler_timezone_utc(mock_reminder_manager, mock_zoneinfo, mock_config):
    """Test that scheduler uses UTC timezone."""
    from ledger_bot.run_ledger_bot import start_bot

    # Simulate ZoneInfo working
    mock_tz = Mock()
    mock_zoneinfo.return_value = mock_tz

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.Config") as mock_config_class:
        mock_config_class.load = Mock(return_value=mock_config)

        with patch("ledger_bot.run_ledger_bot.setup_database"):
            with patch("ledger_bot.run_ledger_bot.LedgerBot"):
                with patch("ledger_bot.run_ledger_bot.setup_slash"):
                    with patch(
                        "ledger_bot.run_ledger_bot.asyncio.get_event_loop"
                    ) as mock_loop:
                        with patch(
                            "ledger_bot.run_ledger_bot.AsyncIOScheduler"
                        ) as mock_scheduler:
                            mock_loop.return_value.run_until_complete = Mock(
                                side_effect=_close_coroutine
                            )

                            start_bot()

                            # Verify scheduler was created with timezone
                            mock_scheduler.assert_called_once()
                            call_kwargs = mock_scheduler.call_args[1]
                            assert "timezone" in call_kwargs


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_signal_handlers_unix(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that signal handlers ARE added on Unix platforms."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot"):
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_event_loop = Mock()
                mock_event_loop.add_signal_handler = Mock()
                mock_event_loop.run_until_complete = Mock(side_effect=_close_coroutine)
                mock_loop.return_value = mock_event_loop

                start_bot()

                # On Unix, signal handlers should be added for SIGINT and SIGTERM
                assert mock_event_loop.add_signal_handler.call_count == 2


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_passes_client_to_reminder_manager(
    mock_reminder_manager_class, mock_setup_database, mock_config_class, mock_config
):
    """Test that the client is passed to the reminder manager."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    mock_reminder_manager = Mock()
    mock_reminder_manager.set_client = Mock()
    mock_reminder_manager_class.return_value = mock_reminder_manager

    with patch("ledger_bot.run_ledger_bot.LedgerBot") as mock_ledger_bot:
        mock_client = Mock()
        mock_ledger_bot.return_value = mock_client

        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete = Mock(
                    side_effect=_close_coroutine
                )

                start_bot()

                # Verify set_client was called with the created client
                mock_reminder_manager.set_client.assert_called_once_with(mock_client)


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_creates_all_storage_types(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that all storage types are created."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.MemberStorage") as mock_member:
        with patch("ledger_bot.run_ledger_bot.TransactionStorage") as mock_transaction:
            with patch(
                "ledger_bot.run_ledger_bot.BotMessageStorage"
            ) as mock_bot_message:
                with patch(
                    "ledger_bot.run_ledger_bot.ReminderStorage"
                ) as mock_reminder_storage:
                    with patch(
                        "ledger_bot.run_ledger_bot.ReactionRoleStorage"
                    ) as mock_reaction_role:
                        with patch(
                            "ledger_bot.run_ledger_bot.CurrencyStorage"
                        ) as mock_currency:
                            with patch(
                                "ledger_bot.run_ledger_bot.EventStorage"
                            ) as mock_event:
                                with patch(
                                    "ledger_bot.run_ledger_bot.EventMemberStorage"
                                ) as mock_event_member:
                                    with patch(
                                        "ledger_bot.run_ledger_bot.EventRegionStorage"
                                    ) as mock_event_region:
                                        with patch(
                                            "ledger_bot.run_ledger_bot.LedgerBot"
                                        ):
                                            with patch(
                                                "ledger_bot.run_ledger_bot.setup_slash"
                                            ):
                                                with patch(
                                                    "ledger_bot.run_ledger_bot.asyncio.get_event_loop"
                                                ) as mock_loop:
                                                    mock_loop.return_value.run_until_complete = (
                                                        Mock()
                                                    )

                                                    start_bot()

                                                    # Verify all storage types were instantiated
                                                    mock_member.assert_called_once()
                                                    mock_transaction.assert_called_once()
                                                    mock_bot_message.assert_called_once()
                                                    mock_reminder_storage.assert_called_once()
                                                    mock_reaction_role.assert_called_once()
                                                    mock_currency.assert_called_once()
                                                    mock_event.assert_called_once()
                                                    mock_event_member.assert_called_once()
                                                    mock_event_region.assert_called_once()


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_creates_all_service_types(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that all service types are created."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.MemberService") as mock_member:
        with patch("ledger_bot.run_ledger_bot.TransactionService") as mock_transaction:
            with patch(
                "ledger_bot.run_ledger_bot.BotMessageService"
            ) as mock_bot_message:
                with patch(
                    "ledger_bot.run_ledger_bot.ReminderService"
                ) as mock_reminder_service:
                    with patch(
                        "ledger_bot.run_ledger_bot.ReactionRoleService"
                    ) as mock_reaction_role:
                        with patch(
                            "ledger_bot.run_ledger_bot.StatsService"
                        ) as mock_stats:
                            with patch(
                                "ledger_bot.run_ledger_bot.CurrencyService"
                            ) as mock_currency:
                                with patch(
                                    "ledger_bot.run_ledger_bot.EventService"
                                ) as mock_event:
                                    with patch(
                                        "ledger_bot.run_ledger_bot.EventMemberService"
                                    ) as mock_event_member:
                                        with patch(
                                            "ledger_bot.run_ledger_bot.EventRegionService"
                                        ) as mock_event_region:
                                            with patch(
                                                "ledger_bot.run_ledger_bot.LedgerBot"
                                            ):
                                                with patch(
                                                    "ledger_bot.run_ledger_bot.setup_slash"
                                                ):
                                                    with patch(
                                                        "ledger_bot.run_ledger_bot.asyncio.get_event_loop"
                                                    ) as mock_loop:
                                                        mock_loop.return_value.run_until_complete = (
                                                            Mock()
                                                        )

                                                        start_bot()

                                                        # Verify all service types were instantiated
                                                        mock_member.assert_called_once()
                                                        mock_transaction.assert_called_once()
                                                        mock_bot_message.assert_called_once()
                                                        mock_reminder_service.assert_called_once()
                                                        mock_reaction_role.assert_called_once()
                                                        mock_stats.assert_called_once()
                                                        mock_currency.assert_called_once()
                                                        mock_event.assert_called_once()
                                                        mock_event_member.assert_called_once()
                                                        mock_event_region.assert_called_once()


@patch("ledger_bot.run_ledger_bot.ZoneInfo")
@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_scheduler_fallback_to_utc_on_zoneinfo_error(
    mock_reminder_manager,
    mock_setup_database,
    mock_config_class,
    mock_zoneinfo,
    mock_config,
):
    """Test that scheduler falls back to UTC on ZoneInfoNotFoundError."""
    from zoneinfo import ZoneInfoNotFoundError

    from ledger_bot.run_ledger_bot import start_bot

    # Simulate ZoneInfo failure
    mock_zoneinfo.side_effect = ZoneInfoNotFoundError("UTC")

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot"):
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                with patch(
                    "ledger_bot.run_ledger_bot.AsyncIOScheduler"
                ) as mock_scheduler:
                    mock_loop.return_value.run_until_complete = Mock(
                        side_effect=_close_coroutine
                    )

                    start_bot()

                    # Verify scheduler was created with fallback timezone
                    mock_scheduler.assert_called_once()
                    call_kwargs = mock_scheduler.call_args[1]
                    assert "timezone" in call_kwargs
                    # Should be timezone.utc not ZoneInfo
                    from datetime import timezone

                    assert call_kwargs["timezone"] == timezone.utc


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_passes_config_to_services(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that config is passed to all services."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.MemberService") as mock_member_service:
        with patch(
            "ledger_bot.run_ledger_bot.TransactionService"
        ) as mock_transaction_service:
            with patch("ledger_bot.run_ledger_bot.LedgerBot"):
                with patch("ledger_bot.run_ledger_bot.setup_slash"):
                    with patch(
                        "ledger_bot.run_ledger_bot.asyncio.get_event_loop"
                    ) as mock_loop:
                        mock_loop.return_value.run_until_complete = Mock(
                            side_effect=_close_coroutine
                        )

                        start_bot()

                        # Verify services were called with config as second positional arg
                        call_args = mock_member_service.call_args
                        assert call_args[0][1] == mock_config

                        call_args = mock_transaction_service.call_args
                        assert call_args[0][1] == mock_config


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_passes_session_factory_to_services(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that session factory is passed to all services."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.MemberService") as mock_member_service:
        with patch(
            "ledger_bot.run_ledger_bot.TransactionService"
        ) as mock_transaction_service:
            with patch("ledger_bot.run_ledger_bot.LedgerBot"):
                with patch("ledger_bot.run_ledger_bot.setup_slash"):
                    with patch(
                        "ledger_bot.run_ledger_bot.asyncio.get_event_loop"
                    ) as mock_loop:
                        mock_loop.return_value.run_until_complete = Mock(
                            side_effect=_close_coroutine
                        )

                        start_bot()

                        # Verify services were called with session factory
                        call_args = mock_member_service.call_args
                        assert call_args[1]["session_factory"] == mock_session_factory

                        call_args = mock_transaction_service.call_args
                        assert call_args[1]["session_factory"] == mock_session_factory


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_passes_scheduler_to_client(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that scheduler is passed to LedgerBot."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot") as mock_ledger_bot:
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                with patch(
                    "ledger_bot.run_ledger_bot.AsyncIOScheduler"
                ) as mock_scheduler_class:
                    mock_scheduler = Mock()
                    mock_scheduler_class.return_value = mock_scheduler
                    mock_loop.return_value.run_until_complete = Mock(
                        side_effect=_close_coroutine
                    )

                    start_bot()

                    # Verify LedgerBot was called with scheduler
                    call_args = mock_ledger_bot.call_args
                    assert call_args[1]["scheduler"] == mock_scheduler


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_passes_reminder_manager_to_client(
    mock_reminder_manager_class, mock_setup_database, mock_config_class, mock_config
):
    """Test that reminder manager is passed to LedgerBot."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager_class.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot") as mock_ledger_bot:
        with patch("ledger_bot.run_ledger_bot.setup_slash"):
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete = Mock(
                    side_effect=_close_coroutine
                )

                start_bot()

                # Verify LedgerBot was called with reminder manager
                call_args = mock_ledger_bot.call_args
                assert call_args[1]["reminders"] == mock_reminder


@patch("ledger_bot.run_ledger_bot.Config")
@patch("ledger_bot.run_ledger_bot.setup_database")
@patch("ledger_bot.run_ledger_bot.ReminderManager")
def test_start_bot_passes_client_to_setup_slash(
    mock_reminder_manager, mock_setup_database, mock_config_class, mock_config
):
    """Test that client is passed to setup_slash."""
    from ledger_bot.run_ledger_bot import start_bot

    mock_config_class.load = Mock(return_value=mock_config)

    mock_session_factory = Mock()
    mock_setup_database.return_value = mock_session_factory

    # Mock reminder manager
    mock_reminder = Mock()
    mock_reminder.set_client = Mock()
    mock_reminder_manager.return_value = mock_reminder

    with patch("ledger_bot.run_ledger_bot.LedgerBot") as mock_ledger_bot:
        mock_client = Mock()
        mock_ledger_bot.return_value = mock_client

        with patch("ledger_bot.run_ledger_bot.setup_slash") as mock_setup_slash:
            with patch("ledger_bot.run_ledger_bot.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete = Mock(
                    side_effect=_close_coroutine
                )

                start_bot()

                # Verify setup_slash was called with client
                mock_setup_slash.assert_called_once()
                call_args = mock_setup_slash.call_args
                assert call_args[1]["client"] == mock_client
