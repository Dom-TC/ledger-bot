"""Refresh the specified transaction message."""
import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.message_generators import generate_transaction_status_message
from ledger_bot.models import BotMessage, Transaction

from .send_message import send_message

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


async def refresh_transaction(
    client: "LedgerBot", row_id: int, channel_id: int | None
) -> str | None:
    """Removes all existing messages for a given transaction, and creates a new message with the current status."""
    log.info(f"Refreshing transaction: {row_id}")

    # Get transaction record
    transaction_record = await client.transaction_storage.get_transaction_by_row_id(
        row_id=row_id
    )

    if transaction_record is None:
        log.info(f"No transaction found with row_id {row_id}")
        return "No transaction found."

    transaction = Transaction.from_airtable(transaction_record)

    log.debug(f"Transaction: {transaction}")

    # Get all existing bot_messages
    bot_messages = transaction.bot_messages

    # We overwrite this with the channel from the bot_message, if it's provided
    channel = (
        await client.get_or_fetch_channel(channel_id)
        if channel_id is not None
        else None
    )

    # Delete all previous bot messages, if they exist
    if bot_messages is not None:
        for bot_message in bot_messages:
            message_id = (
                bot_message.record_id
                if isinstance(bot_message, BotMessage)
                else bot_message
            )

            bot_message = (
                await client.transaction_storage.find_bot_message_by_record_id(
                    message_id
                )
            )
            log.debug(f"Message: {bot_message}")

            try:
                channel = await client.get_or_fetch_channel(bot_message.channel_id)

                if isinstance(channel, discord.TextChannel):
                    message = await channel.fetch_message(bot_message.bot_message_id)

                    log.info(f"Deleting message: {bot_message.bot_message_id}")
                    await message.delete()

                    log.info(f"Deleting message record: {bot_message.record_id}")
                    await client.transaction_storage.delete_bot_message(
                        bot_message.record_id
                    )
                else:
                    log.info(
                        f"Channel {channel} is not a TextChannel, so has no messages"
                    )
            except discord.errors.Forbidden as error:
                log.error(f"You don't have permission to delete the message: {error}")
            except discord.errors.NotFound as error:
                log.error(f"The message has already been deleted: {error}")

                log.info(f"Deleting message record: {bot_message.record_id}")
                await client.transaction_storage.delete_bot_message(
                    bot_message.record_id
                )
            except discord.errors.HTTPException as error:
                log.error(f"An error occured deleting the message: {error}")

    if channel is None:
        return "I couldn't calculate which channel to post in. Please repeat the command specifying a channel id."

    log.info(
        f"Seller Discord ID: {transaction.seller_discord_id} / {type(transaction.seller_discord_id)}"
    )
    log.info(
        f"Buyer Discord ID: {transaction.buyer_discord_id} / {type(transaction.buyer_discord_id)}"
    )

    if transaction.seller_discord_id is None:
        log.warning("No Seller Discord ID specified. Skipping")
        return None

    if transaction.buyer_discord_id is None:
        log.warning("No Buyer Discord ID specified. Skipping")
        return None

    seller = await client.get_or_fetch_user(transaction.seller_discord_id)
    buyer = await client.get_or_fetch_user(transaction.buyer_discord_id)

    log.info(f"Seller: {seller} / {type(seller)}")
    log.info(f"Buyer: {buyer} / {type(buyer)}")

    # Post new message
    message_contents = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=transaction.wine,
        wine_price=transaction.price,
        config=client.config,
        is_update=True,
        is_approved=transaction.sale_approved,
        is_marked_paid_by_buyer=transaction.buyer_marked_paid,
        is_marked_paid_by_seller=transaction.seller_marked_paid,
        is_marked_delivered_by_buyer=transaction.buyer_marked_delivered,
        is_marked_delivered_by_seller=transaction.seller_marked_delivered,
        is_cancelled=transaction.cancelled,
    )

    await send_message(
        response_contents=message_contents,
        channel=channel,
        target_transaction=transaction,
        previous_message_id=None,
        storage=client.transaction_storage,
        config=client.config,
    )

    return "Successfully refreshed message."
