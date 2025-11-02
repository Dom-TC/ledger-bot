"""Tests for generate_reminder_status_message."""

from unittest.mock import Mock

import pytest

from ledger_bot.message_generators.generate_reminder_status_message import (
    generate_reminder_status_message,
)


def test_generate_reminder_status_message_unapproved(mock_config):
    """Test generating reminder message for unapproved transaction."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=False,
        is_marked_paid_by_buyer=False,
        is_marked_paid_by_seller=False,
        is_marked_delivered_by_buyer=False,
        is_marked_delivered_by_seller=False,
        is_cancelled=False,
    )

    assert mock_seller.mention in message
    assert mock_buyer.mention in message
    assert "Château Test 2020" in message
    assert "£99.99" in message
    assert "**Status**" in message
    assert f"Approved: {mock_config.emojis.status_unconfirmed}" in message
    assert f"Paid:           {mock_config.emojis.status_unconfirmed}" in message
    assert f"Delivered: {mock_config.emojis.status_unconfirmed}" in message


def test_generate_reminder_status_message_approved(mock_config):
    """Test generating reminder message for approved transaction."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=False,
        is_marked_paid_by_seller=False,
        is_marked_delivered_by_buyer=False,
        is_marked_delivered_by_seller=False,
        is_cancelled=False,
    )

    assert f"Approved: {mock_config.emojis.status_confirmed}" in message
    assert f"Paid:           {mock_config.emojis.status_unconfirmed}" in message
    assert f"Delivered: {mock_config.emojis.status_unconfirmed}" in message


def test_generate_reminder_status_message_cancelled(mock_config):
    """Test generating reminder message for cancelled transaction."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=False,
        is_marked_paid_by_buyer=False,
        is_marked_paid_by_seller=False,
        is_marked_delivered_by_buyer=False,
        is_marked_delivered_by_seller=False,
        is_cancelled=True,
    )

    assert f"Approved: {mock_config.emojis.status_cancelled}" in message
    assert f"Paid:           {mock_config.emojis.status_cancelled}" in message
    assert f"Delivered: {mock_config.emojis.status_cancelled}" in message


def test_generate_reminder_status_message_buyer_paid_only(mock_config):
    """Test message when only buyer marked as paid."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=True,
        is_marked_paid_by_seller=False,
        is_marked_delivered_by_buyer=False,
        is_marked_delivered_by_seller=False,
        is_cancelled=False,
    )

    assert f"Paid:           {mock_config.emojis.status_part_confirmed}" in message


def test_generate_reminder_status_message_seller_paid_only(mock_config):
    """Test message when only seller marked as paid."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=False,
        is_marked_paid_by_seller=True,
        is_marked_delivered_by_buyer=False,
        is_marked_delivered_by_seller=False,
        is_cancelled=False,
    )

    assert f"Paid:           {mock_config.emojis.status_part_confirmed}" in message


def test_generate_reminder_status_message_both_paid(mock_config):
    """Test message when both parties marked as paid."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=True,
        is_marked_paid_by_seller=True,
        is_marked_delivered_by_buyer=False,
        is_marked_delivered_by_seller=False,
        is_cancelled=False,
    )

    assert f"Paid:           {mock_config.emojis.status_confirmed}" in message


def test_generate_reminder_status_message_buyer_delivered_only(mock_config):
    """Test message when only buyer marked as delivered."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=True,
        is_marked_paid_by_seller=True,
        is_marked_delivered_by_buyer=True,
        is_marked_delivered_by_seller=False,
        is_cancelled=False,
    )

    assert f"Delivered: {mock_config.emojis.status_part_confirmed}" in message


def test_generate_reminder_status_message_seller_delivered_only(mock_config):
    """Test message when only seller marked as delivered."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=True,
        is_marked_paid_by_seller=True,
        is_marked_delivered_by_buyer=False,
        is_marked_delivered_by_seller=True,
        is_cancelled=False,
    )

    assert f"Delivered: {mock_config.emojis.status_part_confirmed}" in message


def test_generate_reminder_status_message_both_delivered(mock_config):
    """Test message when both parties marked as delivered."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=True,
        is_marked_paid_by_seller=True,
        is_marked_delivered_by_buyer=True,
        is_marked_delivered_by_seller=True,
        is_cancelled=False,
    )

    assert f"Delivered: {mock_config.emojis.status_confirmed}" in message


def test_generate_reminder_status_message_formats_price_correctly(mock_config):
    """Test message formats price to 2 decimal places."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Wine",
        wine_price=123.456,
        config=mock_config,
    )

    # Should round to 2 decimal places
    assert "£123.46" in message


def test_generate_reminder_status_message_includes_wine_name(mock_config):
    """Test message includes wine name."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    wine_name = "Very Expensive Wine 2015"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name=wine_name,
        wine_price=99.99,
        config=mock_config,
    )

    assert wine_name in message
    assert (
        f"**{mock_seller.mention} sold {wine_name} to {mock_buyer.mention}**" in message
    )


def test_generate_reminder_status_message_default_values(mock_config):
    """Test message with default parameter values (all False)."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Wine",
        wine_price=50.0,
        config=mock_config,
    )

    # All should be unconfirmed with default values
    assert f"Approved: {mock_config.emojis.status_unconfirmed}" in message
    assert f"Paid:           {mock_config.emojis.status_unconfirmed}" in message
    assert f"Delivered: {mock_config.emojis.status_unconfirmed}" in message


def test_generate_reminder_status_message_completed_transaction(mock_config):
    """Test message for fully completed transaction."""
    mock_seller = Mock()
    mock_seller.mention = "<@111222333>"
    mock_buyer = Mock()
    mock_buyer.mention = "<@999888777>"

    message = generate_reminder_status_message(
        seller=mock_seller,
        buyer=mock_buyer,
        wine_name="Château Test 2020",
        wine_price=99.99,
        config=mock_config,
        is_approved=True,
        is_marked_paid_by_buyer=True,
        is_marked_paid_by_seller=True,
        is_marked_delivered_by_buyer=True,
        is_marked_delivered_by_seller=True,
        is_cancelled=False,
    )

    assert f"Approved: {mock_config.emojis.status_confirmed}" in message
    assert f"Paid:           {mock_config.emojis.status_confirmed}" in message
    assert f"Delivered: {mock_config.emojis.status_confirmed}" in message
