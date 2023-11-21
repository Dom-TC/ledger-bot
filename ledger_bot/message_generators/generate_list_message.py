"""Generates a message listing a users active transactions."""

import logging
import re
from typing import Dict, List

from ledger_bot.models import BotMessage, Transaction
from ledger_bot.storage import AirtableStorage

log = logging.getLogger(__name__)


async def _get_latest_message_link(transaction: Transaction, storage: AirtableStorage):
    if transaction.bot_messages is None:
        return ""

    latest_message_record_id = transaction.bot_messages[-1]
    message_record = await storage.find_bot_message_by_record_id(
        latest_message_record_id
    )
    message = BotMessage.from_airtable(message_record)

    link = f"- https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.bot_message_id}"
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
    log.debug(f"Building transaction lists with {transactions}")
    transaction_lists = {
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
        log.debug(f"Processing transaction: {transaction}")
        # Add transaction details to transaction_lists split by buyer / seller and transaction status

        is_approved = bool(transaction.sale_approved)
        is_delivered = bool(transaction.buyer_marked_delivered) and bool(
            transaction.seller_marked_delivered
        )
        is_paid = bool(transaction.buyer_marked_paid) and bool(
            transaction.seller_marked_paid
        )
        is_cancelled = bool(transaction.cancelled)

        log.debug(f"Is Approved: {is_approved}")
        log.debug(f"Is Delivered: {is_delivered}")
        log.debug(f"Is Paid: {is_paid}")
        log.debug(f"Is Cancelled: {is_cancelled}")

        # Generate link for last status message
        last_message_link = await _get_latest_message_link(
            transaction=transaction, storage=storage
        )

        # Check whether the user is the buyer or seller
        if int(transaction.seller_discord_id) == user_id:
            log.debug("User is seller")
            section = "selling"
            other_party = transaction.buyer_discord_id
        elif int(transaction.buyer_discord_id) == user_id:
            log.debug("User is buyer")
            section = "buying"
            other_party = transaction.seller_discord_id

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

        # Add transaction payload to correct list
        transaction_lists[section][sub_section].append(
            {
                "wine_name": transaction.wine,
                "price": transaction.price,
                "other_party": other_party,
                "last_message_link": last_message_link,
            }
        )

    return transaction_lists


def _split_message(intro: str, purchases_content: str, sales_content: str) -> List[str]:
    """
    Splits the message content into 2000 character chunks.

    Discord can't accept messages more than 2000 characters, so we have to return long lists as multiple messages.

    Parameters
    ----------
    intro : str
        The intro section
    purchases_content : str
        The purchases section
    sales_content : str
        The sales section

    Returns
    -------
    List[str]
        A list of messages to send
    """
    if len(intro + purchases_content + sales_content) > 1995:
        log.info(
            f"Splitting large message ({len(intro + purchases_content + sales_content)} characters)"
        )
        output = [intro]

        if len(purchases_content) < 2000:
            output.append(purchases_content)
        else:
            # Further split purchases:

            # Remove first line (otherwise it's classed as it's own section and sent as a single message)
            purchases_content = purchases_content[15:]

            sections = re.split(r"\n(?=[A-Za-z ]+:)", purchases_content)

            for i, section in enumerate(sections):
                if i == 0:
                    section = "**Purchases**\n" + section

                output.append(section)

        if len(sales_content) < 2000:
            output.append(sales_content)
        else:
            # Further split sales:

            # Remove first line (otherwise it's classed as it's own section and sent as a single message)
            sales_content = sales_content[11:]

            sections = re.split(r"\n(?=[A-Za-z ]+:)", sales_content)

            for i, section in enumerate(sections):
                if i == 0:
                    section = "**Sales**\n" + section

                output.append(section)

    else:
        output = [intro + purchases_content + sales_content]

    return output


async def generate_list_message(
    transactions: List[Transaction], user_id: int, storage: AirtableStorage
) -> List[str]:
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

    purchases_content = ""
    sales_content = ""

    if len(transactions) == 0:
        intro = "You don't have any transactions."
    else:
        transaction_lists = await _build_transaction_lists(
            transactions=transactions, user_id=user_id, storage=storage
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
                    purchases_content += "\n**Purchases**\n"
                    has_purchases = True

                purchases_content += (
                    f"{category.replace('_', ' ').title().replace('And', 'and')}:\n"
                )

                for item in transaction_lists["buying"][category]:
                    log.debug(f"Generating output for {item}")
                    purchases_content += f"- \"{item['wine_name']}\" from <@{item['other_party']}> for £{item['price']} {item['last_message_link']}\n"
                    purchase_count += 1

        for category in transaction_lists["selling"]:
            log.debug(f"Generating message for sale category: {category}")
            if transaction_lists["selling"][category]:
                # If first category with contents, add title
                if not has_sales:
                    sales_content += "\n**Sales**\n"
                    has_sales = True

                sales_content += (
                    f"{category.replace('_', ' ').title().replace('And', 'and')}:\n"
                )

                for item in transaction_lists["selling"][category]:
                    log.debug(f"Generating output for {item}")
                    sales_content += f"- \"{item['wine_name']}\" to <@{item['other_party']}> for £{item['price']} {item['last_message_link']}\n"
                    sale_count += 1

        intro = ""
        if sale_count and purchase_count:
            intro = f"You have {purchase_count} purchase{'s' if purchase_count > 1 else ''} and {sale_count} sale{'s' if sale_count > 1 else ''}.\n"
        elif purchase_count and not sale_count:
            intro = f"You have {purchase_count} purchase{'s' if purchase_count > 1 else ''}.\n"
        elif sale_count and not purchase_count:
            intro = f"You have {sale_count} sale{'s' if sale_count > 1 else ''}.\n"

    output = _split_message(intro, purchases_content, sales_content)

    return output
