import pytest

from ledger_bot.models import MemberAirtable


def test_member_creation():
    data = {
        "id": "test-123",
        "fields": {
            "row_id": "1",
            "username": "username",
            "discord_id": "1234",
            "nickname": "nick",
            "sell_transactions": ["1", "2"],
            "buy_transactions": ["3", "4"],
            "reminders": ["5", "6"],
            "bot_id": "bot-name",
        },
    }

    member = MemberAirtable.from_airtable(data)
    assert member.record_id == "test-123"
    assert member.row_id == "1"
    assert member.username == "username"
    assert member.discord_id == 1234
    assert member.nickname == "nick"
    assert member.sell_transactions == ["1", "2"]
    assert member.buy_transactions == ["3", "4"]
    assert member.reminders == ["5", "6"]
    assert member.bot_id == "bot-name"


@pytest.mark.skip("Not implemented")
def test_member_creation_missing_fields():
    assert False


@pytest.mark.skip("Not implemented")
def test_member_creation_invalid_types():
    assert False


def test_member_dislayname_has_nick():
    member = MemberAirtable(username="testing", discord_id=123, nickname="nick")
    assert member.display_name == "nick"


def test_member_dislayname_no_nick():
    member = MemberAirtable(username="testing", discord_id=123)
    assert member.display_name == "testing"
