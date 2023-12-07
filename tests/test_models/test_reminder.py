from datetime import datetime

import pytest

from ledger_bot.models import Reminder


@pytest.fixture
def sample_data():
    return {
        "id": "test-123",
        "fields": {
            "row_id": "1",
            "date": "2023-12-03T15:30:45.123456+00:00",
            "member_id": ["1234"],
            "transaction_id": ["transaction_id"],
            "status": "status",
            "bot_id": "bot-name",
        },
    }


def test_reminder_creation(sample_data):
    member = Reminder.from_airtable(sample_data)

    assert member.record_id == "test-123"
    assert member.row_id == "1"
    assert member.date == datetime.strptime(
        "2023-12-03T15:30:45.123456+0000", "%Y-%m-%dT%H:%M:%S.%f%z"
    )
    assert member.member_id == "1234"
    assert member.transaction_id == "transaction_id"
    assert member.status == "status"
    assert member.bot_id == "bot-name"


@pytest.mark.skip("Not implemented")
def test_reminder_creation_missing_fields():
    assert False


@pytest.mark.skip("Not implemented")
def test_reminder_creation_invalid_types():
    assert False


def test_to_airtable_with_default_fields(sample_data):
    reminder_instance = Reminder.from_airtable(sample_data)
    airtable_data = reminder_instance.to_airtable()

    assert airtable_data == sample_data


def test_to_airtable_with_custom_fields(sample_data):
    reminder_instance = Reminder.from_airtable(sample_data)
    fields = ["date", "member_id", "status"]
    airtable_data = reminder_instance.to_airtable(fields=fields)

    assert airtable_data == {
        "id": "test-123",
        "fields": {
            "date": "2023-12-03T15:30:45.123456+00:00",
            "member_id": ["1234"],
            "status": "status",
        },
    }
