"""Cleanup.py."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.models import BotMessage, Transaction
from ledger_bot.storage import AirtableStorage

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot


log = logging.getLogger(__name__)


async def cleanup(client: "LedgerBot", storage: AirtableStorage) -> None:
    """
    Removes messages, message records, and (optionally) transaction records.

    Parameters
    ----------
    client : LedgerBot
        The client
    storage : AirtableStorage
        The storage
    """
    log.info("Running cleanup")

    try:
        transactions = await storage.get_completed_transactions(
            client.config["cleanup_delay_hours"]
        )

        if transactions is None:
            log.info("There are no transactions to remove")
            return
        else:
            log.info(f"Cleaning {len(transactions)} transactions")

            for transaction_record in transactions:
                transaction = Transaction.from_airtable(transaction_record)

                log.info(f"Cleaning transaction {transaction.record_id}")

                # If bot_messages exist, remove them.
                # Because we (optionally) keep transaction records, it's possible transactions exist with no bot record
                if transaction.bot_messages is not None:
                    for bot_message in transaction.bot_messages:
                        bot_message_id = (
                            bot_message.record_id
                            if isinstance(bot_message, BotMessage)
                            else bot_message
                        )

                        try:
                            bot_message_record = (
                                await storage.find_bot_message_by_record_id(
                                    record_id=bot_message_id
                                )
                            )
                            bot_message = BotMessage.from_airtable(bot_message_record)

                            channel = client.get_channel(bot_message.channel_id)

                            if isinstance(channel, discord.TextChannel):

                                message = await channel.fetch_message(
                                    bot_message.bot_message_id
                                )

                                log.info(
                                    f"Deleting message: {bot_message.bot_message_id}"
                                )
                                await message.delete()

                                log.info(f"Deleting message record: {bot_message_id}")
                                await storage.delete_bot_message(bot_message_id)

                        except discord.Forbidden as error:
                            log.error(
                                f"You don't have permission to delete the message: {error}"
                            )
                        except discord.NotFound as error:
                            log.error(f"The message has already been deleted: {error}")
                        except discord.HTTPException as error:
                            log.error(f"An error occured deleting the message: {error}")

                if (
                    client.config["cleanup_removes_transaction_records"]
                    and transaction.record_id is not None
                ):
                    log.info(f"Deleting transaction record: {transaction_record}")
                    await storage.delete_transaction(transaction.record_id)

    except AirTableError as error:
        log.error(f"An error occured deleting the record in AirTable: {error}")
