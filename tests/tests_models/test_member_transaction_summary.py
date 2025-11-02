"""Tests for MemberTransactionSummary model."""

from ledger_bot.models.member_transaction_summary import MemberTransactionSummary


class TestMemberTransactionSummary:
    """Test MemberTransactionSummary dataclass."""

    def test_member_transaction_summary_creation(self):
        """Test MemberTransactionSummary can be created with all fields."""
        summary = MemberTransactionSummary(
            sales_count=10,
            purchases_count=15,
            completed_count=20,
            cancelled_count=3,
            open_count=2,
        )

        assert summary.sales_count == 10
        assert summary.purchases_count == 15
        assert summary.completed_count == 20
        assert summary.cancelled_count == 3
        assert summary.open_count == 2

    def test_member_transaction_summary_with_zeros(self):
        """Test MemberTransactionSummary with zero values."""
        summary = MemberTransactionSummary(
            sales_count=0,
            purchases_count=0,
            completed_count=0,
            cancelled_count=0,
            open_count=0,
        )

        assert summary.sales_count == 0
        assert summary.purchases_count == 0
        assert summary.completed_count == 0
        assert summary.cancelled_count == 0
        assert summary.open_count == 0
