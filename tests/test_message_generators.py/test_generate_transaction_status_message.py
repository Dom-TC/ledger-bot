import pytest

from ledger_bot.message_generators import generate_transaction_status_message
from tests.helpers import MockMember


@pytest.fixture()
def emoji_config():
    return {
        "emojis": {
            "approval": "👍",
            "cancel": "👎",
            "paid": "💸",
            "delivered": "🚚",
            "reminder": "🔔",
            "status_confirmed": "🟩",
            "status_part_confirmed": "🟨",
            "status_unconfirmed": "🟥",
            "status_cancelled": "❌",
        }
    }


@pytest.mark.parametrize(
    "wine_name, expected_name",
    [("test", "test"), (None, "None"), ("", ""), (1, "1")],
)
def test_generate_new_transaction_message_paramatise_name(
    wine_name, expected_name, emoji_config
):
    seller = MockMember(id=123)
    buyer = MockMember(id=456)
    wine_price = 1.00
    transaction_id = "123"

    result = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=wine_price,
        config=emoji_config,
        transaction_id=transaction_id,
    )

    assert "New Sale Listed" in result
    assert f"**{seller.mention} sold {expected_name} to {buyer.mention}**" in result
    assert f"Price: £{wine_price}" in result
    assert (
        f"Approved: 🟥 {buyer.mention} please approve this sale by reacting with 👍"
        in result
    )
    assert "Paid:           🟥" in result
    assert "Delivered: 🟥" in result
    assert "To cancel this transaction, please react with 👎" in result
    assert (
        "To set a reminder for this transaction, please react with 🔔 and follow the DMed instructions."
        in result
    )
    assert "Transaction ID: 123" in result


@pytest.mark.parametrize(
    "price, expected_price",
    [
        (1, "1.00"),
        (1.0, "1.00"),
        (1.00, "1.00"),
        (1.000, "1.00"),
        (1.009, "1.01"),
        (123.456, "123.46"),
    ],
)
def test_generate_new_transaction_message_paramatise_price(
    price, expected_price, emoji_config
):
    seller = MockMember(id=123)
    buyer = MockMember(id=456)
    wine_name = "test"
    transaction_id = "123"

    result = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=price,
        config=emoji_config,
        transaction_id=transaction_id,
    )

    assert "New Sale Listed" in result
    assert f"**{seller.mention} sold {wine_name} to {buyer.mention}**" in result
    assert f"Price: £{expected_price}" in result
    assert (
        f"Approved: 🟥 {buyer.mention} please approve this sale by reacting with 👍"
        in result
    )
    assert "Paid:           🟥" in result
    assert "Delivered: 🟥" in result
    assert "To cancel this transaction, please react with 👎" in result
    assert (
        "To set a reminder for this transaction, please react with 🔔 and follow the DMed instructions."
        in result
    )
    assert "Transaction ID: 123" in result


def test_generate_new_transaction_message_approved(emoji_config):
    seller = MockMember(id=123)
    buyer = MockMember(id=456)
    wine_name = "test"
    price = 12.34
    transaction_id = "123"

    result = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=price,
        config=emoji_config,
        is_approved=True,
        is_update=True,
        transaction_id=transaction_id,
    )

    assert "Sale Updated" in result
    assert f"**{seller.mention} sold {wine_name} to {buyer.mention}**" in result
    assert f"Price: £{price}" in result
    assert f"Approved: 🟩\n" in result
    assert "Paid:           🟥 to mark this as paid, please react with 💸" in result
    assert "Delivered: 🟥 to mark this as delivered, please react with 🚚" in result
    assert "To cancel this transaction, please react with 👎" not in result
    assert (
        "To set a reminder for this transaction, please react with 🔔 and follow the DMed instructions."
        in result
    )
    assert "Transaction ID: 123" in result


@pytest.mark.parametrize(
    "buyer_paid, seller_paid, output_line",
    [
        (False, False, "🟥 to mark this as paid, please react with 💸"),
        (
            True,
            False,
            "🟨 @member please confirm this transaction has been paid by reacting with 💸",
        ),
        (
            False,
            True,
            "🟨 @member please confirm this transaction has been paid by reacting with 💸",
        ),
        (True, True, "🟩"),
    ],
)
def test_generate_new_transaction_paid(
    buyer_paid, seller_paid, output_line, emoji_config
):
    seller = MockMember(id=123)
    buyer = MockMember(id=456)
    wine_name = "test"
    price = 12.34

    result = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=price,
        config=emoji_config,
        is_approved=True,
        is_update=True,
        is_marked_paid_by_buyer=buyer_paid,
        is_marked_paid_by_seller=seller_paid,
    )

    assert "Sale Updated" in result
    assert f"**{seller.mention} sold {wine_name} to {buyer.mention}**" in result
    assert f"Price: £{price}" in result
    assert f"Approved: 🟩\n" in result
    assert f"Paid:           {output_line}\n" in result
    assert "Delivered: 🟥 to mark this as delivered, please react with 🚚" in result
    assert "To cancel this transaction, please react with 👎" not in result
    assert (
        "To set a reminder for this transaction, please react with 🔔 and follow the DMed instructions."
        in result
    )
    assert "Transaction ID:" not in result


@pytest.mark.parametrize(
    "buyer_delivered, seller_delivered, output_line",
    [
        (False, False, "🟥 to mark this as delivered, please react with 🚚"),
        (
            True,
            False,
            "🟨 @member please confirm this transaction has been delivered by reacting with 🚚",
        ),
        (
            False,
            True,
            "🟨 @member please confirm this transaction has been delivered by reacting with 🚚",
        ),
        (True, True, "🟩"),
    ],
)
def test_generate_new_transaction_delivered(
    buyer_delivered, seller_delivered, output_line, emoji_config
):
    seller = MockMember(id=123)
    buyer = MockMember(id=456)
    wine_name = "test"
    price = 12.34
    transaction_id = "123"

    result = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=price,
        config=emoji_config,
        is_approved=True,
        is_update=True,
        is_marked_delivered_by_buyer=buyer_delivered,
        is_marked_delivered_by_seller=seller_delivered,
        transaction_id=transaction_id,
    )

    assert "Sale Updated" in result
    assert f"**{seller.mention} sold {wine_name} to {buyer.mention}**" in result
    assert f"Price: £{price}" in result
    assert "Approved: 🟩\n" in result
    assert "Paid:           🟥 to mark this as paid, please react with 💸" in result
    assert f"Delivered: {output_line}\n" in result
    assert "To cancel this transaction, please react with 👎" not in result
    assert (
        "To set a reminder for this transaction, please react with 🔔 and follow the DMed instructions."
        in result
    )
    assert "Transaction ID: 123" in result


def test_generate_new_transaction_completed(emoji_config):
    seller = MockMember(id=123)
    buyer = MockMember(id=456)
    wine_name = "test"
    price = 12.34
    transaction_id = "123"

    result = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=price,
        config=emoji_config,
        is_approved=True,
        is_update=True,
        is_marked_delivered_by_buyer=True,
        is_marked_delivered_by_seller=True,
        is_marked_paid_by_buyer=True,
        is_marked_paid_by_seller=True,
        transaction_id=transaction_id,
    )

    assert "Sale Completed" in result
    assert f"**{seller.mention} sold {wine_name} to {buyer.mention}**" in result
    assert f"Price: £{price}" in result
    assert "Approved: 🟩\n" in result
    assert "Paid:           🟩\n" in result
    assert f"Delivered: 🟩\n" in result
    assert "To cancel this transaction, please react with 👎" not in result
    assert (
        "To set a reminder for this transaction, please react with 🔔 and follow the DMed instructions."
        not in result
    )
    assert "Transaction ID: 123" in result


def pytest_generate_tests(metafunc):
    if metafunc.function == test_generate_new_transaction_cancelled:
        metafunc.parametrize("is_approved", [True, False])
        metafunc.parametrize("is_update", [True, False])
        metafunc.parametrize("is_buyer_delivered", [True, False])
        metafunc.parametrize("is_seller_delivered", [True, False])
        metafunc.parametrize("is_buyer_paid", [True, False])
        metafunc.parametrize("is_seller_paid", [True, False])


def test_generate_new_transaction_cancelled(
    is_approved,
    is_update,
    is_buyer_delivered,
    is_seller_delivered,
    is_buyer_paid,
    is_seller_paid,
    emoji_config,
):
    seller = MockMember(id=123)
    buyer = MockMember(id=456)
    wine_name = "test"
    price = 12.34
    transaction_id = "123"

    result = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=wine_name,
        wine_price=price,
        config=emoji_config,
        is_cancelled=True,
        is_approved=is_approved,
        is_update=is_update,
        is_marked_delivered_by_buyer=is_buyer_delivered,
        is_marked_delivered_by_seller=is_seller_delivered,
        is_marked_paid_by_buyer=is_buyer_paid,
        is_marked_paid_by_seller=is_seller_paid,
        transaction_id=transaction_id,
    )

    assert "Sale Cancelled" in result
    assert f"**{seller.mention} sold {wine_name} to {buyer.mention}**" in result
    assert f"Price: £{price}" in result
    assert "Approved: ❌\n" in result
    assert "Paid:           ❌\n" in result
    assert f"Delivered: ❌\n" in result
    assert "To cancel this transaction, please react with 👎" not in result
    assert (
        "To set a reminder for this transaction, please react with 🔔 and follow the DMed instructions."
        not in result
    )
    assert "Transaction ID: 123" in result
