"""Cleanup.py."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.services import Service

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot


log = logging.getLogger(__name__)


async def cleanup(client: "LedgerBot", service: Service) -> None:
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

    transactions = await service.transaction.get_completed_transaction(
        client.config.cleanup_delay_hours
    )

    if transactions is None:
        log.info("There are no transactions to remove")
        return
    else:
        log.info(f"Cleaning {len(transactions)} transactions")

        for transaction in transactions:
            log.info(f"Cleaning transaction {transaction.id}")

            # If bot_messages exist, remove them.
            # Because we (optionally) keep transaction records, it's possible transactions exist with no bot record
            if transaction.bot_messages is not None:
                for bot_message in transaction.bot_messages:
                    try:
                        channel = await client.get_or_fetch_channel(
                            bot_message.channel_id
                        )

                        if isinstance(channel, discord.TextChannel):

                            message = await channel.fetch_message(
                                bot_message.message_id
                            )

                            log.info(f"Deleting message: {bot_message.message_id}")
                            await message.delete()

                            log.info(f"Deleting message record: {bot_message.id}")
                            await service.bot_message.delete_bot_message(
                                bot_message=bot_message
                            )

                    except discord.Forbidden as error:
                        log.error(
                            f"You don't have permission to delete the message: {error}"
                        )
                    except discord.NotFound as error:
                        log.error(f"The message has already been deleted: {error}")
                    except discord.HTTPException as error:
                        log.error(f"An error occured deleting the message: {error}")

            if (
                client.config.cleanup_removes_transaction_records
                and transaction.id is not None
            ):
                log.info(f"Deleting transaction record: {transaction}")
                await service.transaction.delete_transaction(transaction)
