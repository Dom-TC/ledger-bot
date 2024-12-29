# test_transaction.py
from ast import literal_eval
from datetime import datetime

import pytest

from ledger_bot.models import Event, EventDeposit, EventWine, Member


@pytest.fixture
def sample_event_data():
    return {
        "id": "12345",
        "fields": {
            "row_id": "56789",
            "event_name": "event name",
            "host": "host123",
            "event_date": "2023-12-03T15:30:45.123456+00:00",
            "max_guests": "24",
            "guests": ["guest 1", "guest 2"],
            "guests_count": "2",
            "is_private": False,
            "location": "event location",
            "channel_id": "channel 123",
            "is_archived": False,
            "deposit_amount": "123.43",
            "event_deposits": ["deposit 1", "deposit 2"],
            "event_wines": ["wine 1", "wine 2"],
            "creation_date": "2023-10-03T15:30:45.123456+00:00",
            "archived_date": "2023-11-03T15:30:45.123456+00:00",
            "bot_id": "test-bot-id",
        },
    }


@pytest.fixture
def mock_member(mocker):
    modcked_member = mocker.MagicMock(name="Member", spec=Member)
    return modcked_member


@pytest.fixture
def mock_event_deposit(mocker):
    mocked_event_deposit = mocker.MagicMock(name="EventDeposit", spec=EventDeposit)
    return mocked_event_deposit


@pytest.fixture
def mock_event_wine(mocker):
    mocked_event_wine = mocker.MagicMock(name="EventWine", spec=EventWine)
    return mocked_event_wine


def test_event_creation(sample_event_data):
    event = Event.from_airtable(sample_event_data)

    assert event.record_id == "12345"
    assert isinstance(event.record_id, str)

    assert event.row_id == "56789"
    assert isinstance(event.row_id, str)

    assert event.event_name == "event name"
    assert event.host == "host123"
    assert event.event_date == datetime.strptime(
        "2023-12-03T15:30:45.123456+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
    )
    assert event.max_guests == 24
    assert event.guests == ["guest 1", "guest 2"]
    assert event.guests_count == 2
    assert event.is_private is False
    assert event.location == "event location"
    assert event.channel_id == "channel 123"
    assert event.is_archived is False
    assert event.deposit_amount == 123.43
    assert isinstance(event.deposit_amount, float)

    assert event.event_deposits == ["deposit 1", "deposit 2"]
    assert event.event_wines == ["wine 1", "wine 2"]
    assert event.creation_date == datetime.strptime(
        "2023-10-03T15:30:45.123456+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
    )
    assert event.archived_date == datetime.strptime(
        "2023-11-03T15:30:45.123456+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
    )
    assert event.bot_id == "test-bot-id"


@pytest.mark.skip("Not implemented")
def test_event_creation_missing_fields():
    assert False


@pytest.mark.skip("Not implemented")
def test_event_creation_invalid_types():
    assert False


def test_to_airtable_with_default_fields(sample_event_data):
    event_instance = Event.from_airtable(sample_event_data)
    airtable_data = event_instance.to_airtable()

    assert airtable_data == {
        "id": "12345",
        "fields": {
            "event_name": "event name",
            "host": "host123",
            "event_date": "2023-12-03 15:30:45.123456+00:00",
            "max_guests": "24",
            "guests": ["guest 1", "guest 2"],
            "is_private": False,
            "location": "event location",
            "channel_id": "channel 123",
            "is_archived": False,
            "deposit_amount": "123.43",
            "event_deposits": ["deposit 1", "deposit 2"],
            "event_wines": ["wine 1", "wine 2"],
            "creation_date": "2023-10-03 15:30:45.123456+00:00",
            "archived_date": "2023-11-03 15:30:45.123456+00:00",
            "bot_id": "test-bot-id",
        },
    }


def test_to_airtable_with_custom_fields(sample_event_data):
    fields = ["host", "event_name"]
    event_instance = Event.from_airtable(sample_event_data)
    airtable_data = event_instance.to_airtable(fields=fields)

    assert airtable_data == {
        "id": "12345",
        "fields": {
            "host": "host123",
            "event_name": "event name",
        },
    }


def test_to_airtable_with_member(mock_member):
    mock_member.record_id = "mocked_member_record_id"

    transaction_instance = Event(
        record_id="12345",
        event_name="event name",
        host=mock_member,
        event_date=datetime.strptime(
            "2023-10-03T15:30:45.123456+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
        ),
    )

    airtable_data = transaction_instance.to_airtable(fields=["host"])

    assert airtable_data == {
        "id": "12345",
        "fields": {"host": "mocked_member_record_id"},
    }


def test_to_airtable_with_deposit(mock_event_deposit):
    mock_event_deposit.record_id = "mocked_event_deposit_record_id"

    transaction_instance = Event(
        record_id="12345",
        event_name="event name",
        host="host id",
        event_date=datetime.strptime(
            "2023-10-03T15:30:45.123456+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
        ),
        event_deposits=[mock_event_deposit, "event_deposit_str"],
    )

    airtable_data = transaction_instance.to_airtable(fields=["event_deposits"])

    assert airtable_data == {
        "id": "12345",
        "fields": {
            "event_deposits": ["mocked_event_deposit_record_id", "event_deposit_str"]
        },
    }


def test_to_airtable_with_wines(mock_event_wine):
    mock_event_wine.record_id = "mocked_event_wine_record_id"

    transaction_instance = Event(
        record_id="12345",
        event_name="event name",
        host="host id",
        event_date=datetime.strptime(
            "2023-10-03T15:30:45.123456+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
        ),
        event_wines=[mock_event_wine, "event_wine_str"],
    )

    airtable_data = transaction_instance.to_airtable(fields=["event_wines"])

    assert airtable_data == {
        "id": "12345",
        "fields": {"event_wines": ["mocked_event_wine_record_id", "event_wine_str"]},
    }


def test_from_airtable_required_fields():
    data = {
        "id": "12345",
        "fields": {
            "row_id": "56789",
            "event_name": "event name",
            "host": "event host",
            "event_date": "2023-10-03T15:30:45.123456+00:00",
        },
    }

    event = Event.from_airtable(data)

    assert event.record_id == "12345"
    assert event.row_id == "56789"
    assert event.event_name == "event name"
    assert event.host == "event host"
    assert event.event_date == datetime.strptime(
        "2023-10-03T15:30:45.123456+00:00", "%Y-%m-%dT%H:%M:%S.%f%z"
    )
    assert event.max_guests == None
    assert event.guests == None
    assert event.guests_count == 0
    assert event.is_private is False
    assert event.location == None
    assert event.channel_id == None
    assert event.is_archived is False
    assert event.deposit_amount == None
    assert event.event_deposits == None
    assert event.event_wines == None
    assert event.creation_date == None
    assert event.archived_date == None
    assert event.bot_id == None
