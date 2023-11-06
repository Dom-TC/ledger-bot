"""Generates a message listing a users active transactions."""

import logging
from typing import Dict, List

from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage, BotMessage

log = logging.getLogger(__name__)


async def _get_latest_message_link(transaction: Transaction, storage: AirtableStorage):
    latest_message_record_id = transaction.bot_messages[-1]
    message_record = await storage.find_bot_message_by_record_id(
        latest_message_record_id
    )
    message = BotMessage.from_airtable(message_record)

    link = f"https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.bot_message_id}"
    return link


async def _build_transaction_lists(
    transactions: List[Transaction], user_id: int, storage: AirtableStorage
) -> Dict:
    """
    Converts a list of transactions into a filtered dictionary.

    Each transaction is returned as a dict with keys:
    - wine_name
    - price
    - other_party
    - last_message_link
    """
    transaction_lists = {
        "buying": {
            "awaiting_approval": [],
            "awaiting_payment": [],
            "awaiting_delivery": [],
            "awaiting_payment_and_delivery": [],
            "completed": [],
        },
        "selling": {
            "awaiting_approval": [],
            "awaiting_payment": [],
            "awaiting_delivery": [],
            "awaiting_payment_and_delivery": [],
            "completed": [],
        },
    }

    # Filter transactions
    for transaction in transactions:
        # Add transaction details to transaction_lists split by buyer / seller and transaction status

        is_approved = bool(transaction.sale_approved)
        is_delivered = bool(transaction.buyer_marked_delivered) and bool(
            transaction.seller_marked_delivered
        )
        is_paid = bool(transaction.buyer_marked_paid) and bool(
            transaction.seller_marked_paid
        )

        if int(transaction.seller_discord_id) == user_id:
            # User is seller
            if not is_approved:
                # Not Approved
                last_message_link = await _get_latest_message_link(
                    transaction=transaction, storage=storage
                )

                transaction_lists["selling"]["awaiting_approval"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.buyer_discord_id,
                        "last_message_link": last_message_link,
                    }
                )
            elif is_paid and not is_delivered:
                # Paid but not delivered
                transaction_lists["selling"]["awaiting_delivery"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.buyer_discord_id,
                        "last_message_link": _get_latest_message_link(
                            transaction_id=transaction, storage=storage
                        ),
                    }
                )

            elif is_delivered and not is_paid:
                # Delivered but not paid
                transaction_lists["selling"]["awaiting_payment"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.buyer_discord_id,
                        "last_message_link": _get_latest_message_link(
                            transaction_id=transaction, storage=storage
                        ),
                    }
                )

            elif not is_paid and not is_delivered:
                # Neither paid nor delivered
                transaction_lists["selling"]["awaiting_payment_and_delivery"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.buyer_discord_id,
                        "last_message_link": _get_latest_message_link(
                            transaction_id=transaction, storage=storage
                        ),
                    }
                )

        elif int(transaction.buyer_discord_id) == user_id:
            # User is buyer
            if not is_approved:
                # Not Approved
                last_message_link = await _get_latest_message_link(
                    transaction=transaction, storage=storage
                )

                transaction_lists["buying"]["awaiting_approval"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.seller_discord_id,
                        "last_message_link": last_message_link,
                    }
                )
            elif is_paid and not is_delivered:
                # Paid but not delivered
                transaction_lists["buying"]["awaiting_delivery"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.seller_discord_id,
                        "last_message_link": _get_latest_message_link(
                            transaction_id=transaction, storage=storage
                        ),
                    }
                )

            elif is_delivered and not is_paid:
                # Delivered but not paid
                transaction_lists["buying"]["awaiting_payment"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.seller_discord_id,
                        "last_message_link": _get_latest_message_link(
                            transaction_id=transaction, storage=storage
                        ),
                    }
                )

            elif not is_paid and not is_delivered:
                # Neither paid nor delivered
                transaction_lists["buying"]["awaiting_payment_and_delivery"].append(
                    {
                        "wine_name": transaction.wine,
                        "price": transaction.price,
                        "other_party": transaction.seller_discord_id,
                        "last_message_link": _get_latest_message_link(
                            transaction_id=transaction, storage=storage
                        ),
                    }
                )
    return transaction_lists


async def generate_list_message(
    transactions: List[Transaction], user_id: int, storage: AirtableStorage
) -> str:
    """
    Generates formatted text for listing the provided transactions to return to the user.

    Parameters
    ----------
    transactions : List[Transaction]
        A list of Transactions

    user_id : int
        The id of the user who sent the message

    storage : AirtableStorage
        The storage set

    Returns
    -------
    str
        The text to be sent to the user
    """
    log.info(f"Formatting {len(transactions)} transactions into list")

    contents = ""

    if len(transactions) == 0:
        contents = "You don't have any open transactions."
    else:
        transaction_lists = _build_transaction_lists(transactions, user_id)

        # Produce Output
        has_purchases = False
        has_sales = False
        purchase_count = 0
        sale_count = 0

        for category in transaction_lists["buying"]:
            if transaction_lists["buying"][category]:
                # If first category with contents, add title
                if not has_purchases:
                    contents += "**Purchases**\n"
                    has_purchases = True

                contents += f"{category.replace('_', ' ').title()}:\n"

                for item in transaction_lists["buying"][category]:
                    contents += f"- {item['wine_name']} from <@{item['other_party']}> for {item['price']} - {item['last_message_link']}\n"
                    purchase_count += 1

        for category in transaction_lists["selling"]:
            if transaction_lists["selling"][category]:
                # If first category with contents, add title
                if not has_sales:
                    contents += "**Sales**\n"
                    has_sales = True

                contents += f"{category.replace('_', ' ').title()}:\n"

                for item in transaction_lists["selling"][category]:
                    contents += f"- {item['wine_name']} to <@{item['other_party']}> for {item['price']} - {item['last_message_link']}\n"
                    sale_count += 1

        intro = ""
        if sale_count and purchase_count:
            intro = f"You have {purchase_count} open purchase{'s' if purchase_count > 1 else ''} and {sale_count} open sale{'s' if sale_count > 1 else ''}.\n\n"
        elif purchase_count and not sale_count:
            intro = f"You have {purchase_count} open purchase{'s' if purchase_count > 1 else ''}.\n\n"
        elif sale_count and not purchase_count:
            intro = (
                f"You have {sale_count} open sale{'s' if sale_count > 1 else ''}.\n\n"
            )

    return intro + contents
