from unittest.mock import patch

from ledger_bot.process_dm import is_dm
from tests.helpers import MockDMChannel, MockMessage, MockTextChannel


def test_is_dm_with_dm_channel():
    dm_channel = MockDMChannel()
    message = MockMessage(channel=dm_channel)
    result = is_dm(message)
    assert result is True


def test_is_dm_with_text_channel():
    text_channel = MockTextChannel()
    message = MockMessage(channel=text_channel)
    result = is_dm(message)
    assert result is False


def test_is_dm_with_no_channel():
    message = MockMessage()
    result = is_dm(message)
    assert result is False
