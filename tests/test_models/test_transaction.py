# test_transaction.py
from ast import literal_eval

import pytest

from ledger_bot.models import BotMessage, Reminder, Transaction


@pytest.fixture
def sample_transaction_data():
    return {
        "id": "12345",
        "fields": {
            "row_id": "56789",
            "seller_id": ["seller123"],
            "seller_discord_id": ["123"],
            "buyer_id": ["buyer456"],
            "buyer_discord_id": ["456"],
            "wine": "Wine",
            "price": "50.0",
            "sale_approved": True,
            "buyer_marked_delivered": False,
            "seller_marked_delivered": True,
            "buyer_marked_paid": False,
            "seller_marked_paid": True,
            "cancelled": False,
            "creation_date": "2023-12-03T15:30:45.123456+00:00",
            "approved_date": "2023-12-03T15:30:45.123456+00:00",
            "paid_date": "2023-12-03T15:30:45.123456+00:00",
            "delivered_date": "2023-12-03T15:30:45.123456+00:00",
            "cancelled_date": "2023-12-03T15:30:45.123456+00:00",
            "bot_messages": ["message1", "message2"],
            "reminders": ["reminder1", "reminder2"],
            "bot_id": "bot-id",
        },
    }


@pytest.fixture
def mock_bot_message(mocker):
    mocked_bot_message = mocker.MagicMock(name="BotMessage", spec=BotMessage)
    return mocked_bot_message


@pytest.fixture
def mock_reminder(mocker):
    mocked_bot_message = mocker.MagicMock(name="Reminder", spec=Reminder)
    return mocked_bot_message


def test_transaction_creation(sample_transaction_data):
    transaction = Transaction.from_airtable(sample_transaction_data)

    assert transaction.record_id == "12345"
    assert transaction.row_id == "56789"
    assert transaction.seller_id == "seller123"
    assert transaction.seller_discord_id == 123
    assert transaction.buyer_id == "buyer456"
    assert transaction.buyer_discord_id == 456
    assert transaction.wine == "Wine"
    assert transaction.price == 50.0
    assert transaction.sale_approved is True
    assert transaction.buyer_marked_delivered is False
    assert transaction.seller_marked_delivered is True
    assert transaction.buyer_marked_paid is False
    assert transaction.seller_marked_paid is True
    assert transaction.cancelled is False
    assert transaction.creation_date == "2023-12-03T15:30:45.123456+00:00"
    assert transaction.approved_date == "2023-12-03T15:30:45.123456+00:00"
    assert transaction.paid_date == "2023-12-03T15:30:45.123456+00:00"
    assert transaction.delivered_date == "2023-12-03T15:30:45.123456+00:00"
    assert transaction.cancelled_date == "2023-12-03T15:30:45.123456+00:00"
    assert transaction.bot_messages == ["message1", "message2"]
    assert transaction.reminders == ["reminder1", "reminder2"]
    assert transaction.bot_id == "bot-id"


@pytest.mark.skip("Not implemented")
def test_transaction_creation_missing_fields():
    assert False


@pytest.mark.skip("Not implemented")
def test_transaction_creation_invalid_types():
    assert False


def test_to_airtable_with_default_fields(sample_transaction_data):
    transaction_instance = Transaction.from_airtable(sample_transaction_data)
    airtable_data = transaction_instance.to_airtable()

    assert airtable_data == {
        "id": "12345",
        "fields": {
            "seller_id": ["seller123"],
            "buyer_id": ["buyer456"],
            "wine": "Wine",
            "price": 50.0,
            "sale_approved": True,
            "buyer_marked_delivered": False,
            "seller_marked_delivered": True,
            "buyer_marked_paid": False,
            "seller_marked_paid": True,
            "cancelled": False,
            "creation_date": "2023-12-03T15:30:45.123456+00:00",
            "approved_date": "2023-12-03T15:30:45.123456+00:00",
            "paid_date": "2023-12-03T15:30:45.123456+00:00",
            "delivered_date": "2023-12-03T15:30:45.123456+00:00",
            "cancelled_date": "2023-12-03T15:30:45.123456+00:00",
            "bot_id": "bot-id",
        },
    }


def test_to_airtable_with_custom_fields(sample_transaction_data):
    fields = ["wine", "price"]
    transaction_instance = Transaction.from_airtable(sample_transaction_data)
    airtable_data = transaction_instance.to_airtable(fields=fields)

    assert airtable_data == {
        "id": "12345",
        "fields": {
            "wine": "Wine",
            "price": 50.0,
        },
    }


def test_to_airtable_with_bot_messages(mock_bot_message):
    mock_bot_message.record_id = "mocked_bot_record_id"

    transaction_instance = Transaction(
        record_id="12345",
        seller_id="123",
        buyer_id="456",
        wine="testing",
        price=123.45,
        bot_messages=[mock_bot_message, "str_bot_message"],
    )

    airtable_data = transaction_instance.to_airtable(fields=["bot_messages"])

    assert airtable_data == {
        "id": "12345",
        "fields": {
            "bot_messages": ["mocked_bot_record_id", "str_bot_message"],
        },
    }


@pytest.mark.skip("To Fix")
def test_to_airtable_with_reminder(mock_reminder):
    mock_reminder.record_id = "mocked_reminder_record_id"

    transaction_instance = Transaction(
        record_id="12345",
        seller_id="123",
        buyer_id="456",
        wine="testing",
        price=123.45,
        reminders=[mock_reminder, "str_reminder"],
    )

    airtable_data = transaction_instance.to_airtable(fields=["reminders"])

    assert airtable_data == {
        "id": "12345",
        "fields": {
            "reminders": ["mocked_reminder_record_id", "str_reminder"],
        },
    }


def test_from_airtable_minimal_fields():
    data = {
        "id": "12345",
        "fields": {
            "row_id": "56789",
            "seller_id": ["seller123"],
            "seller_discord_id": ["123"],
            "buyer_id": ["buyer456"],
            "buyer_discord_id": ["456"],
            "wine": "Wine",
            "price": "50.0",
            "bot_id": "bot-id",
        },
    }

    transaction = Transaction.from_airtable(data)

    assert transaction.record_id == "12345"
    assert transaction.row_id == "56789"
    assert transaction.seller_id == "seller123"
    assert transaction.seller_discord_id == 123
    assert transaction.buyer_id == "buyer456"
    assert transaction.buyer_discord_id == 456
    assert transaction.wine == "Wine"
    assert transaction.price == 50.0
    assert transaction.sale_approved is False
    assert transaction.buyer_marked_delivered is False
    assert transaction.seller_marked_delivered is False
    assert transaction.buyer_marked_paid is False
    assert transaction.seller_marked_paid is False
    assert transaction.cancelled is False
    assert transaction.creation_date == None
    assert transaction.approved_date == None
    assert transaction.paid_date == None
    assert transaction.delivered_date == None
    assert transaction.cancelled_date == None
    assert transaction.bot_messages == None
    assert transaction.reminders == None
    assert transaction.bot_id == "bot-id"
