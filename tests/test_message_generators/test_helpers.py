"""Tests for helpers."""

from ledger_bot.message_generators.helpers import (
    is_or_are,
    pluralise_word,
)


def test_is_or_are_singular():
    """Test is_or_are returns 'is' for quantity of 1."""
    assert is_or_are(1) == "is"


def test_is_or_are_plural():
    """Test is_or_are returns 'are' for quantity other than 1."""
    assert is_or_are(0) == "are"
    assert is_or_are(2) == "are"
    assert is_or_are(100) == "are"


def test_pluralise_word_singular():
    """Test pluralise_word returns word unchanged for quantity of 1."""
    assert pluralise_word(1, "one") == "one"
    assert pluralise_word(1, "two") == "two"


def test_pluralise_word_plural():
    """Test pluralise_word returns pluralised word for quantity other than 1."""
    assert pluralise_word(0, "one") == "ones"
    assert pluralise_word(2, "two") == "twos"
    assert pluralise_word(100, "three") == "threes"
