"""Tests for ReminderManager."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, call, patch

import pytest
from apscheduler import events
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ledger_bot.models import Reminder, ReminderStatus
from ledger_bot.reminder_manager import ReminderManager


@pytest.fixture
def mock_scheduler():
    """Create a mock AsyncIOScheduler."""
    scheduler = Mock(spec=AsyncIOScheduler)
    scheduler.add_job = Mock()
    scheduler.add_listener = Mock()
    scheduler.get_job = Mock()
    return scheduler


@pytest.fixture
def mock_service():
    """Create a mock Service."""
    service = Mock()
    service.reminder = Mock()
    service.reminder.list_all_reminders = AsyncMock(return_value=[])
    service.reminder.save_reminder = AsyncMock()
    service.member = Mock()
    service.member.get_or_add_member = AsyncMock()
    service.member.get_member_from_record_id = AsyncMock()
    service.transaction = Mock()
    service.transaction.get_transaction = AsyncMock()
    return service


@pytest.fixture
def reminder_manager(mock_config, mock_scheduler, mock_service):
    """Create a ReminderManager instance."""
    with patch("ledger_bot.reminder_manager.arrow") as mock_arrow:
        mock_now = Mock()
        mock_now.shift.return_value.datetime = datetime(
            2025, 1, 1, 12, 1, 0, tzinfo=timezone.utc
        )
        mock_arrow.utcnow.return_value = mock_now

        manager = ReminderManager(
            config=mock_config,
            scheduler=mock_scheduler,
            service=mock_service,
        )
    return manager


def test_reminder_manager_initialization(
    reminder_manager, mock_scheduler, mock_service, mock_config
):
    """Test ReminderManager initialization."""
    assert reminder_manager.config == mock_config
    assert reminder_manager.scheduler == mock_scheduler
    assert reminder_manager.service == mock_service
    assert reminder_manager.missed_job_ids == []
    assert reminder_manager.get_channel_func is None


def test_reminder_manager_schedules_refresh_on_init(
    mock_scheduler, mock_service, mock_config
):
    """Test that ReminderManager schedules refresh job on initialization."""
    with patch("ledger_bot.reminder_manager.arrow") as mock_arrow:
        mock_now = Mock()
        mock_now.shift.return_value.datetime = datetime(
            2025, 1, 1, 12, 1, 0, tzinfo=timezone.utc
        )
        mock_arrow.utcnow.return_value = mock_now

        manager = ReminderManager(
            config=mock_config,
            scheduler=mock_scheduler,
            service=mock_service,
        )

    # Should schedule the refresh job
    assert mock_scheduler.add_job.called
    call_args = mock_scheduler.add_job.call_args
    assert call_args[1]["name"] == "Refresh Reminders"
    assert call_args[1]["trigger"] == "cron"


def test_reminder_manager_adds_scheduler_listener(
    mock_scheduler, mock_service, mock_config
):
    """Test that ReminderManager adds listener for missed jobs."""
    with patch("ledger_bot.reminder_manager.arrow"):
        manager = ReminderManager(
            config=mock_config,
            scheduler=mock_scheduler,
            service=mock_service,
        )

    # Should add listener for missed jobs
    mock_scheduler.add_listener.assert_called_once()
    call_args = mock_scheduler.add_listener.call_args
    assert call_args[0][1] == events.EVENT_JOB_MISSED


def test_set_client(reminder_manager):
    """Test setting the client."""
    mock_client = Mock()

    reminder_manager.set_client(mock_client)

    assert reminder_manager.client == mock_client


def test_handle_scheduler_event_reminder_job_missed(reminder_manager, mock_scheduler):
    """Test handling missed reminder job event."""
    mock_job = Mock()
    mock_job.name = "Reminder: 123"
    mock_scheduler.get_job.return_value = mock_job

    mock_event = Mock(spec=events.JobEvent)
    mock_event.job_id = "reminder-123"

    reminder_manager.handle_scheduler_event(mock_event)

    assert "reminder-123" in reminder_manager.missed_job_ids


def test_handle_scheduler_event_non_reminder_job(reminder_manager, mock_scheduler):
    """Test handling missed non-reminder job event."""
    mock_job = Mock()
    mock_job.name = "Some Other Job"
    mock_scheduler.get_job.return_value = mock_job

    mock_event = Mock(spec=events.JobEvent)
    mock_event.job_id = "other-job-123"

    reminder_manager.handle_scheduler_event(mock_event)

    # Should not add to missed_job_ids
    assert "other-job-123" not in reminder_manager.missed_job_ids


def test_handle_scheduler_event_job_not_found(reminder_manager, mock_scheduler):
    """Test handling event when job is not found."""
    mock_scheduler.get_job.return_value = None

    mock_event = Mock(spec=events.JobEvent)
    mock_event.job_id = "missing-job"

    # Should not crash
    reminder_manager.handle_scheduler_event(mock_event)

    assert "missing-job" not in reminder_manager.missed_job_ids


@pytest.mark.asyncio
async def test_refresh_reminders_empty_list(
    reminder_manager, mock_service, mock_scheduler
):
    """Test refreshing reminders with empty list."""
    mock_service.reminder.list_all_reminders.return_value = []

    await reminder_manager.refresh_reminders()

    # Should call list_all_reminders
    mock_service.reminder.list_all_reminders.assert_called_once()

    # Should not schedule any jobs (refresh job already added in init)
    # Check that add_job was only called once (during init)
    assert mock_scheduler.add_job.call_count == 1


@pytest.mark.asyncio
async def test_refresh_reminders_with_reminders(
    reminder_manager, mock_service, mock_scheduler
):
    """Test refreshing reminders with active reminders."""
    reminder1 = Reminder(
        id=1,
        reminder_date=datetime(2025, 1, 15, 12, 0, tzinfo=timezone.utc),
        member_id=123,
        transaction_id=456,
        category=ReminderStatus.APPROVED,
    )
    reminder2 = Reminder(
        id=2,
        reminder_date=datetime(2025, 1, 20, 15, 30, tzinfo=timezone.utc),
        member_id=124,
        transaction_id=457,
        category=ReminderStatus.PAID,
    )

    mock_service.reminder.list_all_reminders.return_value = [reminder1, reminder2]

    await reminder_manager.refresh_reminders()

    # Should schedule jobs for both reminders
    # 1 from init + 2 from refresh
    assert mock_scheduler.add_job.call_count == 3

    # Check that jobs were scheduled with correct parameters
    calls = mock_scheduler.add_job.call_args_list

    # Skip first call (init), check the reminder jobs
    reminder_calls = calls[1:]

    assert reminder_calls[0][1]["id"] == "reminder-1"
    assert reminder_calls[0][1]["name"] == "Reminder: 1"
    assert reminder_calls[0][1]["trigger"] == "date"
    assert reminder_calls[0][1]["next_run_time"] == reminder1.reminder_date

    assert reminder_calls[1][1]["id"] == "reminder-2"
    assert reminder_calls[1][1]["name"] == "Reminder: 2"


@pytest.mark.asyncio
async def test_send_reminder_member_not_found(reminder_manager, mock_service):
    """Test send_reminder when member is not found."""
    mock_service.member.get_member_from_record_id.return_value = None

    # Should return early without error
    await reminder_manager.send_reminder(
        reminder_id="123",
        member_id="456",
        transaction_id="789",
        status="approved",
    )

    mock_service.member.get_member_from_record_id.assert_called_once_with(456)


@pytest.mark.asyncio
async def test_send_reminder_transaction_not_found(reminder_manager, mock_service):
    """Test send_reminder when transaction is not found."""
    mock_member = Mock()
    mock_member.discord_id = 999
    mock_service.member.get_member_from_record_id.return_value = mock_member

    mock_user = Mock()
    mock_client = Mock()
    mock_client.get_or_fetch_user = AsyncMock(return_value=mock_user)
    reminder_manager.client = mock_client

    mock_service.transaction.get_transaction.return_value = None

    # Should return early without error
    await reminder_manager.send_reminder(
        reminder_id="123",
        member_id="456",
        transaction_id="789",
        status="approved",
    )

    mock_service.transaction.get_transaction.assert_called_once_with(789)


@pytest.mark.asyncio
async def test_send_reminder_skip_if_approved(reminder_manager, mock_service):
    """Test send_reminder skips if status filter is 'approved' and transaction is approved."""
    mock_member = Mock()
    mock_member.discord_id = 999
    mock_service.member.get_member_from_record_id.return_value = mock_member

    mock_user = Mock()
    mock_user.send = AsyncMock()
    mock_client = Mock()
    mock_client.get_or_fetch_user = AsyncMock(return_value=mock_user)
    reminder_manager.client = mock_client

    mock_transaction = Mock()
    mock_transaction.sale_approved = True  # Already approved
    mock_service.transaction.get_transaction.return_value = mock_transaction

    await reminder_manager.send_reminder(
        reminder_id="123",
        member_id="456",
        transaction_id="789",
        status="approved",
    )

    # Should not send message
    mock_user.send.assert_not_called()


@pytest.mark.asyncio
async def test_send_reminder_skip_if_completed(reminder_manager, mock_service):
    """Test send_reminder skips if status filter is 'completed' and transaction is completed."""
    mock_member = Mock()
    mock_member.discord_id = 999
    mock_service.member.get_member_from_record_id.return_value = mock_member

    mock_user = Mock()
    mock_user.send = AsyncMock()
    mock_client = Mock()
    mock_client.get_or_fetch_user = AsyncMock(return_value=mock_user)
    reminder_manager.client = mock_client

    mock_transaction = Mock()
    mock_transaction.sale_approved = True
    mock_transaction.buyer_paid = True
    mock_transaction.seller_paid = True
    mock_transaction.buyer_delivered = True
    mock_transaction.seller_delivered = True
    mock_service.transaction.get_transaction.return_value = mock_transaction

    await reminder_manager.send_reminder(
        reminder_id="123",
        member_id="456",
        transaction_id="789",
        status="completed",
    )

    # Should not send message
    mock_user.send.assert_not_called()


@pytest.mark.asyncio
@patch("ledger_bot.reminder_manager.generate_reminder_status_message")
async def test_send_reminder_success(
    mock_generate_message, reminder_manager, mock_service
):
    """Test successful reminder sending."""
    mock_member = Mock()
    mock_member.discord_id = 999
    mock_service.member.get_member_from_record_id.return_value = mock_member

    mock_user = Mock()
    mock_user.name = "TestUser"
    mock_user.send = AsyncMock()

    mock_seller_user = Mock()
    mock_buyer_user = Mock()

    mock_client = Mock()
    mock_client.get_or_fetch_user = AsyncMock(
        side_effect=[mock_user, mock_seller_user, mock_buyer_user]
    )
    reminder_manager.client = mock_client

    mock_seller = Mock()
    mock_seller.discord_id = 111
    mock_buyer = Mock()
    mock_buyer.discord_id = 222

    mock_transaction = Mock()
    mock_transaction.sale_approved = False
    mock_transaction.buyer_paid = False
    mock_transaction.seller_paid = False
    mock_transaction.buyer_delivered = False
    mock_transaction.seller_delivered = False
    mock_transaction.cancelled = False
    mock_transaction.wine = "Test Wine"
    mock_transaction.price = 99.99
    mock_transaction.seller = mock_seller
    mock_transaction.buyer = mock_buyer
    mock_transaction.bot_messages = None

    mock_service.transaction.get_transaction.return_value = mock_transaction

    mock_generate_message.return_value = "Test reminder message"

    await reminder_manager.send_reminder(
        reminder_id="123",
        member_id="456",
        transaction_id="789",
        status=None,
    )

    # Should send message
    mock_user.send.assert_called_once()
    sent_message = mock_user.send.call_args[0][0]
    assert "This is your scheduled reminder" in sent_message
    assert "Test reminder message" in sent_message


@pytest.mark.asyncio
@patch("ledger_bot.reminder_manager.generate_reminder_status_message")
async def test_send_reminder_includes_message_link(
    mock_generate_message, reminder_manager, mock_service
):
    """Test reminder includes link to Discord message."""
    mock_member = Mock()
    mock_member.discord_id = 999
    mock_service.member.get_member_from_record_id.return_value = mock_member

    mock_user = Mock()
    mock_user.name = "TestUser"
    mock_user.send = AsyncMock()

    mock_seller_user = Mock()
    mock_buyer_user = Mock()

    mock_client = Mock()
    mock_client.get_or_fetch_user = AsyncMock(
        side_effect=[mock_user, mock_seller_user, mock_buyer_user]
    )
    reminder_manager.client = mock_client

    mock_seller = Mock()
    mock_seller.discord_id = 111
    mock_buyer = Mock()
    mock_buyer.discord_id = 222

    mock_bot_message = Mock()
    mock_bot_message.guild_id = 123456
    mock_bot_message.channel_id = 789012
    mock_bot_message.message_id = 345678

    mock_transaction = Mock()
    mock_transaction.sale_approved = False
    mock_transaction.buyer_paid = False
    mock_transaction.seller_paid = False
    mock_transaction.buyer_delivered = False
    mock_transaction.seller_delivered = False
    mock_transaction.cancelled = False
    mock_transaction.wine = "Test Wine"
    mock_transaction.price = 99.99
    mock_transaction.seller = mock_seller
    mock_transaction.buyer = mock_buyer
    mock_transaction.bot_messages = [mock_bot_message]

    mock_service.transaction.get_transaction.return_value = mock_transaction

    mock_generate_message.return_value = "Test reminder message"

    await reminder_manager.send_reminder(
        reminder_id="123",
        member_id="456",
        transaction_id="789",
        status=None,
    )

    # Should include Discord message link
    sent_message = mock_user.send.call_args[0][0]
    assert "discord.com/channels/123456/789012/345678" in sent_message


@pytest.mark.asyncio
async def test_create_reminder_with_reminder_object(reminder_manager, mock_service):
    """Test creating reminder with pre-built Reminder object."""
    reminder = Reminder(
        reminder_date=datetime(2025, 2, 1, 12, 0, tzinfo=timezone.utc),
        member_id=123,
        transaction_id=456,
        category=ReminderStatus.PAID,
    )

    mock_created_reminder = Mock()
    mock_created_reminder.id = 789
    mock_service.reminder.save_reminder.return_value = mock_created_reminder

    result = await reminder_manager.create_reminder(reminder=reminder)

    assert result == mock_created_reminder
    mock_service.reminder.save_reminder.assert_called_once()


@pytest.mark.asyncio
async def test_create_reminder_with_components(reminder_manager, mock_service):
    """Test creating reminder from components."""
    mock_member_discord = Mock()
    mock_member_discord.id = 999

    mock_member_record = Mock()
    mock_member_record.id = 123
    mock_service.member.get_or_add_member.return_value = mock_member_record

    mock_transaction = Mock()
    mock_transaction.id = 456

    mock_created_reminder = Mock()
    mock_created_reminder.id = 789
    mock_service.reminder.save_reminder.return_value = mock_created_reminder

    reminder_date = datetime(2025, 2, 1, 12, 0, tzinfo=timezone.utc)

    result = await reminder_manager.create_reminder(
        reminder=None,
        date=reminder_date,
        member=mock_member_discord,
        transaction=mock_transaction,
        status="paid",
    )

    assert result == mock_created_reminder
    mock_service.member.get_or_add_member.assert_called_once_with(mock_member_discord)
    mock_service.reminder.save_reminder.assert_called_once()


@pytest.mark.asyncio
async def test_create_reminder_missing_components_raises_error(reminder_manager):
    """Test creating reminder without all required components raises ValueError."""
    with pytest.raises(ValueError):
        await reminder_manager.create_reminder(
            reminder=None,
            date=None,  # Missing required component
            member=Mock(),
            transaction=Mock(),
        )


@pytest.mark.asyncio
async def test_create_reminder_transaction_without_id_raises_error(
    reminder_manager, mock_service
):
    """Test creating reminder with transaction that has no ID raises ValueError."""
    mock_member = Mock()
    mock_member_record = Mock()
    mock_service.member.get_or_add_member.return_value = mock_member_record

    mock_transaction = Mock()
    mock_transaction.id = None  # No ID

    with pytest.raises(ValueError):
        await reminder_manager.create_reminder(
            reminder=None,
            date=datetime(2025, 2, 1, 12, 0, tzinfo=timezone.utc),
            member=mock_member,
            transaction=mock_transaction,
        )


@pytest.mark.asyncio
async def test_list_reminders_not_implemented(reminder_manager):
    """Test list_reminders raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await reminder_manager.list_reminders()


@pytest.mark.asyncio
async def test_remove_reminder_not_implemented(reminder_manager):
    """Test remove_reminder raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await reminder_manager.remove_reminder()
