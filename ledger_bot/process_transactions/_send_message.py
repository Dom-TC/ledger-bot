import logging

import discord

from ledger_bot.errors import AirTableError
from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

log = logging.getLogger(__name__)


async def _send_message(
    response_contents: str,
    channel,
    target_transaction: Transaction,
    previous_message_id: int,
    storage: AirtableStorage,
    config: dict,
):
    """Helper to send messages after updating transactions."""
    log.info("Attempting to send message")
    try:
        sent_message = await channel.send(response_contents)
        await storage.record_bot_message(
            message=sent_message, transaction=target_transaction
        )

    except discord.Forbidden as error:
        log.error(f"You don't have permission to send to that channel: {error}")
    except discord.HTTPException as error:
        log.error(f"An error occured sending the message: {error}")
    except AirTableError as error:
        log.error(f"An error occured storing the content in AirTable: {error}")

    if config["delete_previous_bot_messages"]:
        log.info("delete_previous_bot_messages is true")
        log.info(f"Removing bot_message {previous_message_id}")
        old_message = await channel.fetch_message(previous_message_id)

        try:
            await old_message.delete()
            previous_message_id = old_message.id
            previous_bot_message_record = await storage.find_bot_message_by_message_id(
                str(previous_message_id)
            )
            previous_bot_message_record_id = previous_bot_message_record["id"]
            await storage.delete_bot_message(previous_bot_message_record_id)
        except discord.Forbidden as error:
            log.error(f"You don't have permission to send to that channel: {error}")
        except discord.NotFound as error:
            log.error(f"The message has already been deleted: {error}")
        except discord.HTTPException as error:
            log.error(f"An error occured deleting the message: {error}")
        except AirTableError as error:
            log.error(f"An error occured deleting the record in AirTable: {error}")
