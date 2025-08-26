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
    client: "LedgerBot", record_id: int, channel_id: int | None
) -> str | None:
    """Removes all existing messages for a given transaction, and creates a new message with the current status."""
    log.info(f"Refreshing transaction: {record_id}")

    # Get transaction record
    transaction = await client.service.transaction.get_transaction(record_id=record_id)

    if transaction is None:
        log.info(f"No transaction found with row_id {record_id}")
        return "No transaction found."

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
            log.debug(f"Message: {bot_message}")

            try:
                channel = await client.get_or_fetch_channel(bot_message.channel_id)

                if isinstance(channel, discord.TextChannel):
                    message = await channel.fetch_message(bot_message.message_id)

                    log.info(f"Deleting message: {bot_message.message_id}")
                    await message.delete()

                    log.info(f"Deleting message record: {bot_message.id}")
                    await client.service.bot_message.delete_bot_message(bot_message)
                else:
                    log.info(
                        f"Channel {channel} is not a TextChannel, so has no messages"
                    )
            except discord.errors.Forbidden as error:
                log.error(f"You don't have permission to delete the message: {error}")
            except discord.errors.NotFound as error:
                log.error(f"The message has already been deleted: {error}")

                log.info(f"Deleting message record: {bot_message.id}")
                await client.service.bot_message.delete_bot_message(bot_message)
            except discord.errors.HTTPException as error:
                log.error(f"An error occured deleting the message: {error}")

    if channel is None:
        return "I couldn't calculate which channel to post in. Please repeat the command specifying a channel id."

    log.info(
        f"Seller Discord ID: {transaction.seller.discord_id} / {type(transaction.seller.discord_id)}"
    )
    log.info(
        f"Buyer Discord ID: {transaction.buyer.discord_id} / {type(transaction.buyer.discord_id)}"
    )

    if transaction.seller.discord_id is None:
        log.warning("No Seller Discord ID specified. Skipping")
        return None

    if transaction.buyer.discord_id is None:
        log.warning("No Buyer Discord ID specified. Skipping")
        return None

    seller = await client.get_or_fetch_user(transaction.seller.discord_id)
    buyer = await client.get_or_fetch_user(transaction.buyer.discord_id)

    log.info(f"Seller: {seller} / {type(seller)}")
    log.info(f"Buyer: {buyer} / {type(buyer)}")

    # Post new message
    message_contents = await generate_transaction_status_message(
        transaction=transaction,
        client=client,
        config=client.config,
        is_update=True,
    )

    await send_message(
        response_contents=message_contents,
        channel=channel,
        target_transaction=transaction,
        previous_message_id=None,
        service=client.service,
        config=client.config,
    )

    return "Successfully refreshed message."
