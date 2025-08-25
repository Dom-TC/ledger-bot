import pytest

from ledger_bot.models import BotMessageAirtable


def test_bot_message_creation():
    data = {
        "id": "rec123",
        "fields": {
            "row_id": "row123",
            "bot_message_id": 987,
            "channel_id": 123,
            "guild_id": 456,
            "transaction_id": ["trans456"],
            "message_creation_date": "2022-01-01T12:34:56Z",
            "bot_id": "bot789",
        },
    }
    bot_message = BotMessageAirtable.from_airtable(data)

    assert bot_message.record_id == "rec123"
    assert bot_message.row_id == "row123"
    assert bot_message.bot_message_id == 987
    assert bot_message.channel_id == 123
    assert bot_message.guild_id == 456
    assert bot_message.transaction_id == "trans456"
    assert bot_message.message_creation_date == "2022-01-01T12:34:56Z"
    assert bot_message.bot_id == "bot789"


@pytest.mark.skip("Not implemented")
def test_bot_message_creation_missing_fields():
    assert False


def test_bot_message_creation_invalid_types():
    data = {"id": "rec123", "fields": {"bot_message_id": 987, "channel_id": 123}}
    with pytest.raises(TypeError) as excinfo:
        BotMessageAirtable.from_airtable(data)

    assert (
        str(excinfo.value)
        == "int() argument must be a string, a bytes-like object or a real number, not 'NoneType'"
    )
