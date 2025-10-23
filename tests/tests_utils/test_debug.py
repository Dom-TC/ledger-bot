import logging

import pytest

from ledger_bot.utils import debug


def test_debug_decorator_logs_and_returns(caplog):
    @debug
    def add(a, b):
        """Add two numbers."""
        return a + b

    with caplog.at_level(logging.DEBUG):
        result = add(3, 4)

    # The result should be returned normally
    assert result == 7

    # The log should include both 'Calling' and 'returned' lines
    logs = [rec.message for rec in caplog.records]
    assert any("Calling add(3, 4)" in msg for msg in logs)
    assert any("add() returned 7" in msg for msg in logs)


def test_debug_preserves_metadata():
    def original_function(x):
        """Example docstring."""
        return x

    decorated = debug(original_function)

    # functools.wraps should preserve metadata
    assert decorated.__name__ == "original_function"
    assert decorated.__doc__ == "Example docstring."


def test_debug_with_kwargs(caplog):
    @debug
    def greet(name, punctuation="!"):
        return f"Hello {name}{punctuation}"

    with caplog.at_level(logging.DEBUG):
        result = greet("Dom", punctuation="?")

    assert result == "Hello Dom?"
    assert any(
        "Calling greet('Dom', punctuation='?')" in msg for msg in caplog.messages
    )
    assert any("greet() returned 'Hello Dom?'" in msg for msg in caplog.messages)


def test_debug_with_mixed_args_and_kwargs(caplog):
    @debug
    def combine(a, b, sep="-"):
        return f"{a}{sep}{b}"

    with caplog.at_level(logging.DEBUG):
        result = combine("foo", "bar", sep=":")

    assert result == "foo:bar"
    messages = caplog.messages
    assert any("Calling combine('foo', 'bar', sep=':')" in m for m in messages)
    assert any("combine() returned 'foo:bar'" in m for m in messages)


def test_debug_handles_exceptions(caplog):
    @debug
    def fail():
        raise ValueError("bad stuff")

    caplog.set_level(logging.DEBUG)
    with pytest.raises(ValueError, match="bad stuff"):
        fail()

    # Should still log the call line even if exception occurs
    assert "Calling fail()" in caplog.text
    # It shouldn’t log the return value
    assert "fail() returned" not in caplog.text


def test_debug_with_mixed_args(caplog):
    @debug
    def combine(a, b=2, *, c=3):
        return a + b + c

    caplog.set_level(logging.DEBUG)
    result = combine(1, b=5, c=7)

    assert result == 13
    assert "Calling combine(1, b=5, c=7)" in caplog.text
    assert "combine() returned 13" in caplog.text
