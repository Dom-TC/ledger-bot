"""Tests for split_message function."""

import pytest

from ledger_bot.message_generators.split_message import (
    _split_text_on_newline,
    split_message,
)


def test_split_message_short_content():
    """Test that short messages are not split."""
    content = ["Hello", "World", "This is a test"]
    result = split_message(content)

    assert len(result) == 1
    assert result[0] == "Hello\nWorld\nThis is a test"


def test_split_message_empty_content():
    """Test handling of empty content."""
    content = []
    result = split_message(content)

    assert len(result) == 1
    assert result[0] == ""


def test_split_message_single_item():
    """Test handling of single item list."""
    content = ["Single line message"]
    result = split_message(content)

    assert len(result) == 1
    assert result[0] == "Single line message"


def test_split_message_long_content():
    """Test that long messages are split correctly."""
    # Create content that exceeds 1995 characters with newlines for proper splitting
    long_line = "Line\n" * 500  # Creates ~2500 chars with newlines
    content = [long_line]
    result = split_message(content)

    # Should be split into multiple chunks
    assert len(result) > 1
    # Each chunk should be under 2000 chars (implementation uses 1995 limit + some overhead)
    for chunk in result:
        assert len(chunk) <= 2000


def test_split_message_with_sections():
    """Test splitting message with multiple sections."""
    section1 = "Section 1:\n" + ("Line\n" * 100)  # ~600 chars
    section2 = "Section 2:\n" + ("Line\n" * 100)  # ~600 chars
    section3 = "Section 3:\n" + ("Line\n" * 100)  # ~600 chars
    section4 = "Section 4:\n" + ("Line\n" * 100)  # ~600 chars

    content = [section1, section2, section3, section4]
    result = split_message(content)

    # Total is ~2400 chars, should be split
    assert len(result) > 1


def test_split_message_with_empty_strings():
    """Test that empty strings in content are handled."""
    content = ["Hello", "", "World", ""]
    result = split_message(content)

    # Empty strings are kept as they are just joined with newlines for short content
    assert len(result) == 1
    assert result[0] == "Hello\n\nWorld\n"


def test_split_text_on_newline_basic():
    """Test basic splitting on newlines."""
    text = "Line 1\nLine 2\nLine 3"
    chunks = _split_text_on_newline(text, chunk_length=20)

    # Each line is ~7 chars, should fit multiple per chunk
    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk) <= 20


def test_split_text_on_newline_exact_fit():
    """Test splitting when lines exactly fit chunk size."""
    text = "12345\n12345\n12345"
    chunks = _split_text_on_newline(text, chunk_length=12)

    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk) <= 12


def test_split_text_on_newline_single_long_line():
    """Test splitting with a single line exceeding chunk size."""
    text = "A" * 100
    chunks = _split_text_on_newline(text, chunk_length=50)

    # Single line without newlines will exceed chunk size
    # Function splits on first character creating empty first chunk
    assert len(chunks) >= 1
    # All chunks combined should equal original text
    assert "".join(chunks) == text


def test_split_message_preserves_formatting():
    """Test that markdown formatting is preserved."""
    content = [
        "**Bold Title**",
        "Some content",
        "Another line",
    ]
    result = split_message(content)

    assert "**Bold Title**" in result[0]


def test_split_message_max_length():
    """Test that no chunk exceeds Discord's limit."""
    # Create various sizes of content
    content = [
        "Short line",
        "A" * 1000,
        "Medium line " * 50,
        "X" * 500,
    ]

    result = split_message(content)

    for chunk in result:
        assert len(chunk) <= 2000, f"Chunk exceeded 2000 chars: {len(chunk)}"


def test_split_message_very_long_single_section():
    """Test splitting a very long single section."""
    # Create a section with title and lots of content
    content = ["Title:\n" + ("Content line\n" * 200)]  # ~2600 chars

    result = split_message(content)

    # Should be split into multiple messages
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 2000
