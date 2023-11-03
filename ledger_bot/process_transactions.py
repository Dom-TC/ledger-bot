"""Functions to update transaction statuses."""

import datetime
import logging

import discord
from message_generator import generate_transaction_status_message
from models import AirTableError, Transaction
from storage import AirtableStorage

log = logging.getLogger(__name__)


async def approve_transaction(
    reactor: discord.Member,
    buyer: discord.Member,
    seller: discord.Member,
    payload,
    channel,
    target_transaction: Transaction,
    config: dict,
    storage: AirtableStorage,
):
    """
    Approve the specified transaction.

    Paramaters
    ----------
    reactor : discord.Member
        The user who made the reaction
    buyer : discord.Member
        The Member object of the buyer
    seller : discord.Member
        The Member object of the seller
    payload
        The payload of the reaction
    channel
        The channel the transaction was made in
    target_transaction : Transaction
        The transaction being processed
    config : dict
        The config dictionary

    """
    if reactor.id != buyer.id:
        log.info(
            f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Reactor is not the buyer"
        )
        return

    if target_transaction.sale_approved:
        log.info(
            f"Ignoring approval on transaction {target_transaction.row_id}. Transaction already approved"
        )
        return

    target_transaction.sale_approved = True
    target_transaction.approved_date = datetime.datetime.utcnow().isoformat()
    transaction_fields = ["sale_approved", "approved_date"]
    log.debug(f"target_transaction: {target_transaction}")
    await storage.save_transaction(
        transaction=target_transaction, fields=transaction_fields
    )

    response_contents = generate_transaction_status_message(
        seller=seller,
        buyer=buyer,
        wine_name=target_transaction.wine,
        wine_price=target_transaction.price,
        config=config,
        is_update=True,
        is_approved=True,
    )

    try:
        sent_message = await channel.send(response_contents)
        await storage.record_bot_message(
            message=sent_message, transaction=target_transaction
        )

    except discord.HTTPException as error:
        log.error(f"An error occured sending the message: {error}")
    except discord.Forbidden as error:
        log.error(f"You don't have permission to send to that channel: {error}")
    except AirTableError as error:
        log.error(f"An error occured storing the content in AirTable: {error}")

    if config["delete_previous_bot_messages"]:
        log.info("delete_previous_bot_messages is true")
        log.info(f"Removing bot_message {payload.message_id}")
        old_message = await channel.fetch_message(payload.message_id)

        try:
            await old_message.delete()
            previous_message_id = old_message.id
            previous_bot_message_record = await storage.find_bot_message_by_message_id(
                previous_message_id
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
