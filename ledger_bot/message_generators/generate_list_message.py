"""Generates a message listing a users active transactions."""

import logging
from typing import Any, Dict, List

from ledger_bot.models import Transaction
from ledger_bot.services import Service

from .split_message import split_message

log = logging.getLogger(__name__)


async def _get_latest_message_link(
    transaction: Transaction,
) -> str:
    if not transaction.bot_messages:
        return ""

    message = transaction.bot_messages[-1]

    link = f"- https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.message_id}"
    return link


async def _build_transaction_lists(
    transactions: List[Transaction], user_id: int, service: Service
) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Converts a list of transactions into a filtered dictionary.

    Each transaction is returned as a dict with keys:
    - wine_name
    - price
    - other_party
    - last_message_link
    """
    log.debug("Building transaction lists")
    transaction_lists: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        "buying": {
            "awaiting_approval": [],
            "awaiting_payment": [],
            "awaiting_delivery": [],
            "awaiting_payment_and_delivery": [],
            "cancelled": [],
            "completed": [],
        },
        "selling": {
            "awaiting_approval": [],
            "awaiting_payment": [],
            "awaiting_delivery": [],
            "awaiting_payment_and_delivery": [],
            "cancelled": [],
            "completed": [],
        },
    }

    # Filter transactions
    for transaction in transactions:
        # Add transaction details to transaction_lists split by buyer / seller and transaction status

        is_approved = bool(transaction.sale_approved)
        is_delivered = bool(transaction.buyer_delivered) and bool(
            transaction.seller_delivered
        )
        is_paid = bool(transaction.buyer_paid) and bool(transaction.seller_paid)
        is_cancelled = bool(transaction.cancelled)

        # Generate link for last status message
        last_message_link = await _get_latest_message_link(transaction=transaction)

        if transaction.seller.discord_id is None:
            log.warning("No Seller Discord ID specified. Skipping")
            raise ValueError

        if transaction.buyer.discord_id is None:
            log.warning("No Buyer Discord ID specified. Skipping")
            raise ValueError

        # Check whether the user is the buyer or seller
        if int(transaction.seller.discord_id) == user_id:
            section = "selling"
            other_party = transaction.buyer.discord_id
        elif int(transaction.buyer.discord_id) == user_id:
            section = "buying"
            other_party = transaction.seller.discord_id
        else:
            section = "unknown"
            other_party = None

        # Define sub_section
        if is_cancelled:
            sub_section = "cancelled"
        elif not is_approved:
            sub_section = "awaiting_approval"
        elif is_paid and not is_delivered:
            sub_section = "awaiting_delivery"
        elif is_delivered and not is_paid:
            sub_section = "awaiting_payment"
        elif not is_paid and not is_delivered:
            sub_section = "awaiting_payment_and_delivery"
        elif is_paid and is_delivered:
            sub_section = "completed"
        else:
            log.error("Sub-section is unknown")
            sub_section = "unknown"

        # Add transaction payload to correct list
        transaction_lists[section][sub_section].append(
            {
                "wine_name": transaction.wine,
                "price": "{:.2f}".format(transaction.price),
                "other_party": other_party,
                "last_message_link": last_message_link,
            }
        )

    return transaction_lists


async def generate_list_message(
    transactions: List[Transaction], user_id: int, service: Service
) -> List[str]:
    """
    Generates formatted text for listing the provided transactions to return to the user.

    Parameters
    ----------
    transactions : List[Transaction]
        A list of Transactions

    user_id : int
        The id of the user who sent the message

    service : Service
        The services to interface with the database

    Returns
    -------
    str
        The text to be sent to the user
    """
    log.info(f"Formatting {len(transactions)} transactions into list")

    purchases_content = ""
    sales_content = ""

    if len(transactions) == 0:
        intro = "You don't have any transactions."
    else:
        transaction_lists = await _build_transaction_lists(
            transactions=transactions, user_id=user_id, service=service
        )
        # Produce Output
        has_purchases = False
        has_sales = False
        purchase_count = 0
        sale_count = 0

        for category in transaction_lists["buying"]:
            log.debug(f"Generating message for purchase category: {category}")
            if transaction_lists["buying"][category]:
                # If first category with contents, add title
                if not has_purchases:
                    purchases_content += "\n**Purchases**"
                    has_purchases = True

                purchases_content += (
                    f"\n{category.replace('_', ' ').title().replace('And', 'and')}:\n"
                )

                for item in transaction_lists["buying"][category]:
                    purchases_content += f"- \"{item['wine_name']}\" from <@{item['other_party']}> for £{item['price']} {item['last_message_link']}\n"
                    purchase_count += 1

        for category in transaction_lists["selling"]:
            log.debug(f"Generating message for sale category: {category}")
            if transaction_lists["selling"][category]:
                # If first category with contents, add title
                if not has_sales:
                    sales_content += "\n**Sales**"
                    has_sales = True

                sales_content += (
                    f"\n{category.replace('_', ' ').title().replace('And', 'and')}:\n"
                )

                for item in transaction_lists["selling"][category]:
                    sales_content += f"- \"{item['wine_name']}\" to <@{item['other_party']}> for £{item['price']} {item['last_message_link']}\n"
                    sale_count += 1

        intro = ""
        if sale_count and purchase_count:
            intro = f"You have {purchase_count} purchase{'s' if purchase_count > 1 else ''} and {sale_count} sale{'s' if sale_count > 1 else ''}.\n"
        elif purchase_count and not sale_count:
            intro = f"You have {purchase_count} purchase{'s' if purchase_count > 1 else ''}.\n"
        elif sale_count and not purchase_count:
            intro = f"You have {sale_count} sale{'s' if sale_count > 1 else ''}.\n"

    output = split_message([intro, purchases_content, sales_content])
    return output
