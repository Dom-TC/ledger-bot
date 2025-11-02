"""Tests for stats models."""

import pytest

from ledger_bot.models.member import Member
from ledger_bot.models.stats import ServerStats, Stats, TransactionStats


class TestTransactionStats:
    """Test TransactionStats dataclass."""

    def test_transaction_stats_creation(self):
        """Test TransactionStats can be created with all fields."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123456

        stats = TransactionStats(
            unapproved=5,
            approved=10,
            paid=8,
            delivered=7,
            completed=6,
            cancelled=2,
            avg_price=25.50,
            total_price=255.00,
            total_count=20,
            most_expensive_name="Expensive Wine",
            most_expensive_member=mock_member,
            most_expensive_price=150.00,
        )

        assert stats.unapproved == 5
        assert stats.approved == 10
        assert stats.paid == 8
        assert stats.delivered == 7
        assert stats.completed == 6
        assert stats.cancelled == 2
        assert stats.avg_price == 25.50
        assert stats.total_price == 255.00
        assert stats.total_count == 20
        assert stats.most_expensive_name == "Expensive Wine"
        assert stats.most_expensive_member == mock_member
        assert stats.most_expensive_price == 150.00


class TestServerStats:
    """Test ServerStats dataclass."""

    def test_server_stats_creation(self):
        """Test ServerStats can be created with all fields."""
        buyer1 = Member()
        buyer1.username = "buyer1"
        buyer1.discord_id = 1

        seller1 = Member()
        seller1.username = "seller1"
        seller1.discord_id = 2

        stats = ServerStats(
            total_count=100,
            total_value=5000.00,
            avg_price=50.00,
            most_expensive_name="Rare Wine",
            most_expensive_value=500.00,
            top_buyers=[buyer1],
            top_sellers=[seller1],
        )

        assert stats.total_count == 100
        assert stats.total_value == 5000.00
        assert stats.avg_price == 50.00
        assert stats.most_expensive_name == "Rare Wine"
        assert stats.most_expensive_value == 500.00
        assert len(stats.top_buyers) == 1
        assert stats.top_buyers[0] == buyer1
        assert len(stats.top_sellers) == 1
        assert stats.top_sellers[0] == seller1


class TestStats:
    """Test Stats dataclass."""

    def test_stats_creation_with_all_fields(self):
        """Test Stats can be created with all fields."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123

        purchase_stats = TransactionStats(
            unapproved=1,
            approved=2,
            paid=3,
            delivered=4,
            completed=5,
            cancelled=6,
            avg_price=10.0,
            total_price=50.0,
            total_count=5,
            most_expensive_name="Wine A",
            most_expensive_member=mock_member,
            most_expensive_price=20.0,
        )

        sale_stats = TransactionStats(
            unapproved=1,
            approved=2,
            paid=3,
            delivered=4,
            completed=5,
            cancelled=6,
            avg_price=15.0,
            total_price=75.0,
            total_count=5,
            most_expensive_name="Wine B",
            most_expensive_member=mock_member,
            most_expensive_price=30.0,
        )

        server_stats = ServerStats(
            total_count=50,
            total_value=1000.0,
            avg_price=20.0,
            most_expensive_name="Wine C",
            most_expensive_value=100.0,
            top_buyers=[mock_member],
            top_sellers=[mock_member],
        )

        stats = Stats(purchase=purchase_stats, sale=sale_stats, server=server_stats)

        assert stats.purchase == purchase_stats
        assert stats.sale == sale_stats
        assert stats.server == server_stats

    def test_stats_user_total_with_both_purchase_and_sale(self):
        """Test user_total property with both purchase and sale stats."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123

        purchase_stats = TransactionStats(
            unapproved=0,
            approved=0,
            paid=0,
            delivered=0,
            completed=0,
            cancelled=0,
            avg_price=0.0,
            total_price=0.0,
            total_count=5,
            most_expensive_name="",
            most_expensive_member=mock_member,
            most_expensive_price=0.0,
        )

        sale_stats = TransactionStats(
            unapproved=0,
            approved=0,
            paid=0,
            delivered=0,
            completed=0,
            cancelled=0,
            avg_price=0.0,
            total_price=0.0,
            total_count=7,
            most_expensive_name="",
            most_expensive_member=mock_member,
            most_expensive_price=0.0,
        )

        stats = Stats(purchase=purchase_stats, sale=sale_stats, server=None)

        assert stats.user_total == 12

    def test_stats_user_total_with_only_purchase(self):
        """Test user_total property with only purchase stats."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123

        purchase_stats = TransactionStats(
            unapproved=0,
            approved=0,
            paid=0,
            delivered=0,
            completed=0,
            cancelled=0,
            avg_price=0.0,
            total_price=0.0,
            total_count=5,
            most_expensive_name="",
            most_expensive_member=mock_member,
            most_expensive_price=0.0,
        )

        stats = Stats(purchase=purchase_stats, sale=None, server=None)

        assert stats.user_total == 5

    def test_stats_user_total_with_only_sale(self):
        """Test user_total property with only sale stats."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123

        sale_stats = TransactionStats(
            unapproved=0,
            approved=0,
            paid=0,
            delivered=0,
            completed=0,
            cancelled=0,
            avg_price=0.0,
            total_price=0.0,
            total_count=7,
            most_expensive_name="",
            most_expensive_member=mock_member,
            most_expensive_price=0.0,
        )

        stats = Stats(purchase=None, sale=sale_stats, server=None)

        assert stats.user_total == 7

    def test_stats_user_total_with_no_stats(self):
        """Test user_total property with no purchase or sale stats."""
        stats = Stats(purchase=None, sale=None, server=None)

        assert stats.user_total == 0

    def test_stats_user_percentage_with_valid_data(self):
        """Test user_percentage property with valid data."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123

        purchase_stats = TransactionStats(
            unapproved=0,
            approved=0,
            paid=0,
            delivered=0,
            completed=0,
            cancelled=0,
            avg_price=0.0,
            total_price=0.0,
            total_count=10,
            most_expensive_name="",
            most_expensive_member=mock_member,
            most_expensive_price=0.0,
        )

        server_stats = ServerStats(
            total_count=100,
            total_value=0.0,
            avg_price=0.0,
            most_expensive_name="",
            most_expensive_value=0.0,
            top_buyers=[],
            top_sellers=[],
        )

        stats = Stats(purchase=purchase_stats, sale=None, server=server_stats)

        assert stats.user_percentage == 10.0

    def test_stats_user_percentage_with_no_server_stats(self):
        """Test user_percentage property with no server stats."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123

        purchase_stats = TransactionStats(
            unapproved=0,
            approved=0,
            paid=0,
            delivered=0,
            completed=0,
            cancelled=0,
            avg_price=0.0,
            total_price=0.0,
            total_count=10,
            most_expensive_name="",
            most_expensive_member=mock_member,
            most_expensive_price=0.0,
        )

        stats = Stats(purchase=purchase_stats, sale=None, server=None)

        assert stats.user_percentage is None

    def test_stats_user_percentage_with_no_user_stats(self):
        """Test user_percentage property with no user stats."""
        server_stats = ServerStats(
            total_count=100,
            total_value=0.0,
            avg_price=0.0,
            most_expensive_name="",
            most_expensive_value=0.0,
            top_buyers=[],
            top_sellers=[],
        )

        stats = Stats(purchase=None, sale=None, server=server_stats)

        assert stats.user_percentage is None

    def test_stats_user_percentage_with_sale_only(self):
        """Test user_percentage property with sale stats only."""
        mock_member = Member()
        mock_member.username = "test_user"
        mock_member.discord_id = 123

        sale_stats = TransactionStats(
            unapproved=0,
            approved=0,
            paid=0,
            delivered=0,
            completed=0,
            cancelled=0,
            avg_price=0.0,
            total_price=0.0,
            total_count=25,
            most_expensive_name="",
            most_expensive_member=mock_member,
            most_expensive_price=0.0,
        )

        server_stats = ServerStats(
            total_count=200,
            total_value=0.0,
            avg_price=0.0,
            most_expensive_name="",
            most_expensive_value=0.0,
            top_buyers=[],
            top_sellers=[],
        )

        stats = Stats(purchase=None, sale=sale_stats, server=server_stats)

        assert stats.user_percentage == 12.5
