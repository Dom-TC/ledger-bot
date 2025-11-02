"""Tests for helpers."""

from ledger_bot.message_generators.helpers import (
    is_or_are,
    pluralise_word,
)


def test_is_or_are_singular():
    """Test _is_or_are returns 'is' for quantity of 1."""
    assert is_or_are(1) == "is"


def test_is_or_are_plural():
    """Test _is_or_are returns 'are' for quantity other than 1."""
    assert is_or_are(0) == "are"
    assert is_or_are(2) == "are"
    assert is_or_are(100) == "are"


def test_pluralise_word_singular():
    """Test _pluralise_word returns word unchanged for quantity of 1."""
    assert pluralise_word(1, "purchase") == "purchase"
    assert pluralise_word(1, "sale") == "sale"


def test_pluralise_word_plural():
    """Test _pluralise_word returns pluralised word for quantity other than 1."""
    assert pluralise_word(0, "purchase") == "purchases"
    assert pluralise_word(2, "sale") == "sales"
    assert pluralise_word(100, "transaction") == "transactions"
