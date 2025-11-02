"""Helpers for generating messages."""


def is_or_are(qty: int) -> str:
    """Returns is or are depending on whether qty is > 1."""
    return "are" if qty != 1 else "is"


def pluralise_word(qty: int, word: str) -> str:
    """Returns a pluralised version of word if needed."""
    return f"{word}s" if qty != 1 else word
