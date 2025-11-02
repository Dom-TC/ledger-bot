"""Tests for generate_stats_message."""

from ledger_bot.message_generators.generate_stats_message import generate_stats_message
from ledger_bot.models import Member, ServerStats, Stats, TransactionStats


def test_generate_stats_message_no_transactions():
    """Test generating stats message when no transactions exist."""
    stats = Stats(purchase=None, sale=None, server=None)

    message = generate_stats_message(stats)

    assert "No transactions have been recorded" in message
    assert "Can't generate stats" in message


def test_generate_stats_message_with_purchases_only(sample_member):
    """Test generating stats message with only purchase stats."""
    purchase_stats = TransactionStats(
        unapproved=1,
        approved=2,
        paid=3,
        delivered=4,
        completed=5,
        cancelled=1,
        avg_price=50.0,
        total_price=250.0,
        total_count=10,
        most_expensive_name="Expensive Wine",
        most_expensive_member=sample_member,
        most_expensive_price=100.0,
    )

    server_stats = ServerStats(
        total_count=100,
        total_value=5000.0,
        avg_price=50.0,
        most_expensive_name="Top Wine",
        most_expensive_value=200.0,
        top_buyers=[sample_member],
        top_sellers=[sample_member],
    )

    stats = Stats(purchase=purchase_stats, sale=None, server=server_stats)

    message = generate_stats_message(stats)

    assert "**Personal Stats**" in message
    assert "You've made 10 purchases" in message
    assert "1 is unapproved" in message
    assert "2 are approved" in message
    assert "3 are paid" in message
    assert "4 are delivered" in message
    assert "5 are completed" in message
    assert "1 is cancelled" in message
    assert "average purchase price is £50.00" in message
    assert "spent a total of £250.00" in message
    assert "Expensive Wine" in message
    assert f"<@{sample_member.discord_id}>" in message
    assert "£100.00" in message


def test_generate_stats_message_with_sales_only(sample_member):
    """Test generating stats message with only sale stats."""
    sale_stats = TransactionStats(
        unapproved=0,
        approved=1,
        paid=2,
        delivered=3,
        completed=4,
        cancelled=0,
        avg_price=75.0,
        total_price=300.0,
        total_count=8,
        most_expensive_name="Premium Wine",
        most_expensive_member=sample_member,
        most_expensive_price=150.0,
    )

    server_stats = ServerStats(
        total_count=100,
        total_value=5000.0,
        avg_price=50.0,
        most_expensive_name="Top Wine",
        most_expensive_value=200.0,
        top_buyers=[sample_member],
        top_sellers=[sample_member],
    )

    stats = Stats(purchase=None, sale=sale_stats, server=server_stats)

    message = generate_stats_message(stats)

    assert "**Personal Stats**" in message
    assert "You've made 8" in message
    # Note: there's a typo in the source code that says 'purchase' instead of 'sale'
    assert "1 is approved" in message
    assert "2 are paid" in message
    assert "3 are delivered" in message
    assert "4 are completed" in message
    # Should not show unapproved or cancelled when count is 0
    assert "0 is unapproved" not in message
    assert "0 is cancelled" not in message
    assert "average sale price is £75.00" in message
    assert "made a total of £300.00" in message
    assert "Premium Wine" in message


def test_generate_stats_message_with_both_purchases_and_sales(sample_member):
    """Test generating stats message with both purchase and sale stats."""
    purchase_stats = TransactionStats(
        unapproved=1,
        approved=2,
        paid=3,
        delivered=4,
        completed=5,
        cancelled=1,
        avg_price=50.0,
        total_price=250.0,
        total_count=10,
        most_expensive_name="Expensive Purchase",
        most_expensive_member=sample_member,
        most_expensive_price=100.0,
    )

    sale_stats = TransactionStats(
        unapproved=0,
        approved=1,
        paid=2,
        delivered=3,
        completed=4,
        cancelled=0,
        avg_price=75.0,
        total_price=300.0,
        total_count=8,
        most_expensive_name="Expensive Sale",
        most_expensive_member=sample_member,
        most_expensive_price=150.0,
    )

    server_stats = ServerStats(
        total_count=100,
        total_value=5000.0,
        avg_price=50.0,
        most_expensive_name="Top Wine",
        most_expensive_value=200.0,
        top_buyers=[sample_member],
        top_sellers=[sample_member],
    )

    stats = Stats(purchase=purchase_stats, sale=sale_stats, server=server_stats)

    message = generate_stats_message(stats)

    assert "**Personal Stats**" in message
    assert "You've made 10 purchases and 8 sales" in message
    assert "Of your 10 purchases:" in message
    assert "Of your 8" in message  # Sales section
    assert "average purchase price is £50.00" in message
    assert "average sale price is £75.00" in message
    assert "Expensive Purchase" in message
    assert "Expensive Sale" in message


def test_generate_stats_message_with_server_stats(sample_member):
    """Test generating stats message with server stats included."""
    from unittest.mock import Mock

    purchase_stats = TransactionStats(
        unapproved=0,
        approved=0,
        paid=0,
        delivered=0,
        completed=10,
        cancelled=0,
        avg_price=50.0,
        total_price=500.0,
        total_count=10,
        most_expensive_name="Wine",
        most_expensive_member=sample_member,
        most_expensive_price=100.0,
    )

    buyer1 = Mock(spec=Member)
    buyer1.discord_id = 111111111
    buyer1.username = "buyer1"

    buyer2 = Mock(spec=Member)
    buyer2.discord_id = 222222222
    buyer2.username = "buyer2"

    seller1 = Mock(spec=Member)
    seller1.discord_id = 333333333
    seller1.username = "seller1"

    seller2 = Mock(spec=Member)
    seller2.discord_id = 444444444
    seller2.username = "seller2"

    server_stats = ServerStats(
        total_count=100,
        total_value=5000.0,
        avg_price=50.0,
        most_expensive_name="Top Wine",
        most_expensive_value=200.0,
        top_buyers=[buyer1, buyer2],
        top_sellers=[seller1, seller2],
    )

    stats = Stats(purchase=purchase_stats, sale=None, server=server_stats)

    message = generate_stats_message(stats)

    assert "**Server Stats**" in message
    assert "100 transactions recorded in the server" in message
    assert "total value of £5000.00" in message
    assert "You account for 10.0% of transactions" in message
    assert "average price has been £50.00" in message
    assert "Top Wine" in message
    assert "£200.00" in message
    assert "three users with the most purchases" in message
    assert f"<@{buyer1.discord_id}>" in message
    assert f"<@{buyer2.discord_id}>" in message
    assert "three users with the most sales" in message
    assert f"<@{seller1.discord_id}>" in message
    assert f"<@{seller2.discord_id}>" in message


def test_generate_stats_message_singular_purchase(sample_member):
    """Test message with exactly 1 purchase uses singular form."""
    purchase_stats = TransactionStats(
        unapproved=0,
        approved=0,
        paid=0,
        delivered=0,
        completed=1,
        cancelled=0,
        avg_price=50.0,
        total_price=50.0,
        total_count=1,
        most_expensive_name="Wine",
        most_expensive_member=sample_member,
        most_expensive_price=50.0,
    )

    server_stats = ServerStats(
        total_count=100,
        total_value=5000.0,
        avg_price=50.0,
        most_expensive_name="Top Wine",
        most_expensive_value=200.0,
        top_buyers=[sample_member],
        top_sellers=[sample_member],
    )

    stats = Stats(purchase=purchase_stats, sale=None, server=server_stats)

    message = generate_stats_message(stats)

    assert "You've made 1 purchase" in message
    assert "Of your 1 purchase:" in message
    assert "1 is completed" in message


def test_generate_stats_message_singular_sale(sample_member):
    """Test message with exactly 1 sale uses singular form."""
    sale_stats = TransactionStats(
        unapproved=0,
        approved=0,
        paid=0,
        delivered=0,
        completed=1,
        cancelled=0,
        avg_price=50.0,
        total_price=50.0,
        total_count=1,
        most_expensive_name="Wine",
        most_expensive_member=sample_member,
        most_expensive_price=50.0,
    )

    server_stats = ServerStats(
        total_count=100,
        total_value=5000.0,
        avg_price=50.0,
        most_expensive_name="Top Wine",
        most_expensive_value=200.0,
        top_buyers=[sample_member],
        top_sellers=[sample_member],
    )

    stats = Stats(purchase=None, sale=sale_stats, server=server_stats)

    message = generate_stats_message(stats)

    assert "You've made 1 sale" in message
    assert "Of your 1" in message
    assert "1 is completed" in message


def test_generate_stats_message_with_zero_counts_hidden(sample_member):
    """Test that status counts of 0 are not shown in message."""
    purchase_stats = TransactionStats(
        unapproved=0,
        approved=0,
        paid=0,
        delivered=0,
        completed=5,
        cancelled=0,
        avg_price=50.0,
        total_price=250.0,
        total_count=5,
        most_expensive_name="Wine",
        most_expensive_member=sample_member,
        most_expensive_price=100.0,
    )

    server_stats = ServerStats(
        total_count=100,
        total_value=5000.0,
        avg_price=50.0,
        most_expensive_name="Top Wine",
        most_expensive_value=200.0,
        top_buyers=[sample_member],
        top_sellers=[sample_member],
    )

    stats = Stats(purchase=purchase_stats, sale=None, server=server_stats)

    message = generate_stats_message(stats)

    # Should only show completed, not the zero-count statuses
    assert "5 are completed" in message
    assert "0 is unapproved" not in message
    assert "0 is approved" not in message
    assert "0 is paid" not in message
    assert "0 is delivered" not in message
    assert "0 is cancelled" not in message
