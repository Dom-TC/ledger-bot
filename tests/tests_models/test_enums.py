"""Tests for enum models."""

from ledger_bot.models.bot_message import BotMessageType
from ledger_bot.models.event_member import EventMemberStatus
from ledger_bot.models.event_wine import WineCategory, WineSize
from ledger_bot.models.reminder import ReminderStatus


class TestReminderStatus:
    """Test ReminderStatus enum."""

    def test_reminder_status_approved(self):
        """Test ReminderStatus.APPROVED value."""
        assert ReminderStatus.APPROVED.value == "approved"

    def test_reminder_status_cancelled(self):
        """Test ReminderStatus.CANCELLED value."""
        assert ReminderStatus.CANCELLED.value == "cancelled"

    def test_reminder_status_delivered(self):
        """Test ReminderStatus.DELIVERED value."""
        assert ReminderStatus.DELIVERED.value == "delivered"

    def test_reminder_status_paid(self):
        """Test ReminderStatus.PAID value."""
        assert ReminderStatus.PAID.value == "paid"

    def test_reminder_status_completed(self):
        """Test ReminderStatus.COMPLETED value."""
        assert ReminderStatus.COMPLETED.value == "completed"

    def test_reminder_status_all_values(self):
        """Test all ReminderStatus enum members exist."""
        expected = {"APPROVED", "CANCELLED", "DELIVERED", "PAID", "COMPLETED"}
        actual = {status.name for status in ReminderStatus}
        assert actual == expected


class TestBotMessageType:
    """Test BotMessageType enum."""

    def test_bot_message_type_transaction(self):
        """Test BotMessageType.TRANSACTION value."""
        assert BotMessageType.TRANSACTION.value == "transaction"

    def test_bot_message_type_event(self):
        """Test BotMessageType.EVENT value."""
        assert BotMessageType.EVENT.value == "event"

    def test_bot_message_type_all_values(self):
        """Test all BotMessageType enum members exist."""
        expected = {"TRANSACTION", "EVENT"}
        actual = {msg_type.name for msg_type in BotMessageType}
        assert actual == expected


class TestEventMemberStatus:
    """Test EventMemberStatus enum."""

    def test_event_member_status_host(self):
        """Test EventMemberStatus.HOST value."""
        assert EventMemberStatus.HOST.value == "host"

    def test_event_member_status_confirmed(self):
        """Test EventMemberStatus.CONFIRMED value."""
        assert EventMemberStatus.CONFIRMED.value == "confirmed"

    def test_event_member_status_waitlist(self):
        """Test EventMemberStatus.WAITLIST value."""
        assert EventMemberStatus.WAITLIST.value == "waitlist"

    def test_event_member_status_cancelled(self):
        """Test EventMemberStatus.CANCELLED value."""
        assert EventMemberStatus.CANCELLED.value == "cancelled"

    def test_event_member_status_all_values(self):
        """Test all EventMemberStatus enum members exist."""
        expected = {"HOST", "CONFIRMED", "WAITLIST", "CANCELLED"}
        actual = {status.name for status in EventMemberStatus}
        assert actual == expected


class TestWineCategory:
    """Test WineCategory enum."""

    def test_wine_category_sparkling(self):
        """Test WineCategory.SPARKLING value."""
        assert WineCategory.SPARKLING.value == "sparkling"

    def test_wine_category_white(self):
        """Test WineCategory.WHITE value."""
        assert WineCategory.WHITE.value == "white"

    def test_wine_category_red(self):
        """Test WineCategory.RED value."""
        assert WineCategory.RED.value == "red"

    def test_wine_category_sweet(self):
        """Test WineCategory.SWEET value."""
        assert WineCategory.SWEET.value == "sweet"

    def test_wine_category_other(self):
        """Test WineCategory.OTHER value."""
        assert WineCategory.OTHER.value == "other"

    def test_wine_category_all_values(self):
        """Test all WineCategory enum members exist."""
        expected = {"SPARKLING", "WHITE", "RED", "SWEET", "OTHER"}
        actual = {category.name for category in WineCategory}
        assert actual == expected


class TestWineSize:
    """Test WineSize enum."""

    def test_wine_size_half(self):
        """Test WineSize.HALF value."""
        assert WineSize.HALF.value == "37.5"

    def test_wine_size_fiftycl(self):
        """Test WineSize.FIFTYCL value."""
        assert WineSize.FIFTYCL.value == "50"

    def test_wine_size_bottle(self):
        """Test WineSize.BOTTLE value."""
        assert WineSize.BOTTLE.value == "75"

    def test_wine_size_mag(self):
        """Test WineSize.MAG value."""
        assert WineSize.MAG.value == "150"

    def test_wine_size_dmag(self):
        """Test WineSize.DMAG value."""
        assert WineSize.DMAG.value == "300"

    def test_wine_size_all_values(self):
        """Test all WineSize enum members exist."""
        expected = {"HALF", "FIFTYCL", "BOTTLE", "MAG", "DMAG"}
        actual = {size.name for size in WineSize}
        assert actual == expected
