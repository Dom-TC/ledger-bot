"""Generates a message telling a user their stats."""

import logging
from typing import List

import pandas as pd

from ledger_bot.models import Transaction
from ledger_bot.storage import AirtableStorage

log = logging.getLogger(__name__)


def _is_or_are(qty: int) -> str:
    """Returns is or are depending on whether qty is > 1."""
    return "are" if qty != 1 else "is"


def _build_dataframe(transactions: List[Transaction]) -> pd.DataFrame:
    log.debug("Generating dataframe")
    transactions_df = pd.DataFrame(
        [transaction.__dict__ for transaction in transactions]
    )

    # Convert string to float
    transactions_df["price"] = pd.to_numeric(transactions_df["price"], errors="coerce")

    # Convert strings to boolean
    transactions_df["sale_approved"] = transactions_df["sale_approved"].astype(bool)
    transactions_df["buyer_marked_delivered"] = transactions_df[
        "buyer_marked_delivered"
    ].astype(bool)
    transactions_df["seller_marked_delivered"] = transactions_df[
        "seller_marked_delivered"
    ].astype(bool)
    transactions_df["buyer_marked_paid"] = transactions_df["buyer_marked_paid"].astype(
        bool
    )
    transactions_df["seller_marked_paid"] = transactions_df[
        "seller_marked_paid"
    ].astype(bool)
    transactions_df["cancelled"] = transactions_df["cancelled"].astype(bool)

    # Convert strings to datetime
    transactions_df["creation_date"] = pd.to_datetime(transactions_df["creation_date"])
    transactions_df["approved_date"] = pd.to_datetime(transactions_df["approved_date"])
    transactions_df["paid_date"] = pd.to_datetime(transactions_df["paid_date"])
    transactions_df["delivered_date"] = pd.to_datetime(
        transactions_df["delivered_date"]
    )
    transactions_df["cancelled_date"] = pd.to_datetime(
        transactions_df["cancelled_date"]
    )

    # Create summary frames
    transactions_df["is_none_status"] = (
        ~transactions_df["sale_approved"]
        & ~transactions_df["buyer_marked_delivered"]
        & ~transactions_df["seller_marked_delivered"]
        & ~transactions_df["buyer_marked_paid"]
        & ~transactions_df["seller_marked_paid"]
        & ~transactions_df["cancelled"]
    )
    transactions_df["is_approved"] = (
        transactions_df["sale_approved"]
        & ~transactions_df["buyer_marked_delivered"]
        & ~transactions_df["seller_marked_delivered"]
        & ~transactions_df["buyer_marked_paid"]
        & ~transactions_df["seller_marked_paid"]
        & ~transactions_df["cancelled"]
    )
    transactions_df["is_delivered"] = (
        transactions_df["sale_approved"]
        & transactions_df["buyer_marked_delivered"]
        & transactions_df["seller_marked_delivered"]
        & ~transactions_df["buyer_marked_paid"]
        & ~transactions_df["seller_marked_paid"]
        & ~transactions_df["cancelled"]
    )
    transactions_df["is_paid"] = (
        transactions_df["sale_approved"]
        & ~transactions_df["buyer_marked_delivered"]
        & ~transactions_df["seller_marked_delivered"]
        & transactions_df["buyer_marked_paid"]
        & transactions_df["seller_marked_paid"]
        & ~transactions_df["cancelled"]
    )
    transactions_df["is_completed"] = (
        transactions_df["sale_approved"]
        & transactions_df["buyer_marked_delivered"]
        & transactions_df["seller_marked_delivered"]
        & transactions_df["buyer_marked_paid"]
        & transactions_df["seller_marked_paid"]
        & ~transactions_df["cancelled"]
    )
    transactions_df["is_cancelled"] = (
        ~transactions_df["sale_approved"]
        & ~transactions_df["buyer_marked_delivered"]
        & ~transactions_df["seller_marked_delivered"]
        & ~transactions_df["buyer_marked_paid"]
        & ~transactions_df["seller_marked_paid"]
        & transactions_df["cancelled"]
    )

    return transactions_df


def generate_stats_message(
    transactions: List[Transaction], user_id: int, storage: AirtableStorage
) -> str:
    """Generate the message to send one someone uses the stats command."""
    dataframe = _build_dataframe(transactions)

    log.info("Calculating stats")

    # Create user dataframes
    buyer_dataframe = dataframe[dataframe["buyer_discord_id"] == user_id]
    seller_dataframe = dataframe[dataframe["seller_discord_id"] == user_id]

    # User Stats
    user_count_buyer_all = buyer_dataframe.shape[0]
    user_count_seller_all = seller_dataframe.shape[0]

    seller_has_transactions = bool(
        not seller_dataframe[~seller_dataframe["is_cancelled"]].empty
    )
    buyer_has_transactions = bool(
        not buyer_dataframe[~buyer_dataframe["is_cancelled"]].empty
    )

    user_count_buyer_unapproved = buyer_dataframe[
        buyer_dataframe["is_none_status"]
    ].shape[0]
    user_count_buyer_approved = buyer_dataframe[buyer_dataframe["is_approved"]].shape[0]
    user_count_buyer_delivered = buyer_dataframe[buyer_dataframe["is_delivered"]].shape[
        0
    ]
    user_count_buyer_paid = buyer_dataframe[buyer_dataframe["is_paid"]].shape[0]
    user_count_buyer_completed = buyer_dataframe[buyer_dataframe["is_completed"]].shape[
        0
    ]
    user_count_buyer_cancelled = buyer_dataframe[buyer_dataframe["is_cancelled"]].shape[
        0
    ]

    user_count_seller_unapproved = seller_dataframe[
        seller_dataframe["is_none_status"]
    ].shape[0]
    user_count_seller_approved = seller_dataframe[
        seller_dataframe["is_approved"]
    ].shape[0]
    user_count_seller_delivered = seller_dataframe[
        seller_dataframe["is_delivered"]
    ].shape[0]
    user_count_seller_paid = seller_dataframe[seller_dataframe["is_paid"]].shape[0]
    user_count_seller_completed = seller_dataframe[
        seller_dataframe["is_completed"]
    ].shape[0]
    user_count_seller_cancelled = seller_dataframe[
        seller_dataframe["is_cancelled"]
    ].shape[0]

    if buyer_has_transactions:
        user_average_purchase_price = buyer_dataframe[~buyer_dataframe["is_cancelled"]][
            "price"
        ].mean()
        user_total_purchase_price = buyer_dataframe[~buyer_dataframe["is_cancelled"]][
            "price"
        ].sum()

        user_max_purchase_wine_name = buyer_dataframe.loc[
            buyer_dataframe[~buyer_dataframe["is_cancelled"]]["price"].idxmax(), "wine"
        ]
        user_max_purchase_wine_seller = buyer_dataframe.loc[
            buyer_dataframe[~buyer_dataframe["is_cancelled"]]["price"].idxmax(),
            "seller_discord_id",
        ]
        user_max_purchase_wine_price = buyer_dataframe.loc[
            buyer_dataframe[~buyer_dataframe["is_cancelled"]]["price"].idxmax(), "price"
        ]

    if seller_has_transactions:
        user_average_sale_price = seller_dataframe[~seller_dataframe["is_cancelled"]][
            "price"
        ].mean()
        user_total_sale_price = seller_dataframe[~seller_dataframe["is_cancelled"]][
            "price"
        ].sum()

        user_max_sale_wine_name = seller_dataframe.loc[
            seller_dataframe[~seller_dataframe["is_cancelled"]]["price"].idxmax(),
            "wine",
        ]
        user_max_sale_wine_buyer = seller_dataframe.loc[
            seller_dataframe[~seller_dataframe["is_cancelled"]]["price"].idxmax(),
            "buyer_discord_id",
        ]
        user_max_sale_wine_price = seller_dataframe.loc[
            seller_dataframe[~seller_dataframe["is_cancelled"]]["price"].idxmax(),
            "price",
        ]

    # Server Stats
    server_count_all = dataframe.shape[0]
    server_average_price = dataframe[~dataframe["is_cancelled"]]["price"].mean()
    server_total_price = dataframe[~dataframe["is_cancelled"]]["price"].sum()
    server_max_wine_name = dataframe.loc[
        dataframe[~dataframe["is_cancelled"]]["price"].idxmax(), "wine"
    ]
    server_max_wine_price = dataframe.loc[
        dataframe[~dataframe["is_cancelled"]]["price"].idxmax(), "price"
    ]
    server_max_wine_buyer = dataframe.loc[
        dataframe[~dataframe["is_cancelled"]]["price"].idxmax(), "buyer_discord_id"
    ]
    server_max_wine_seller = dataframe.loc[
        dataframe[~dataframe["is_cancelled"]]["price"].idxmax(), "seller_discord_id"
    ]

    top_buyers = dataframe["buyer_discord_id"].value_counts().head(3)
    top_buyers_output = ""
    for buyer_discord_id, count in top_buyers.items():
        top_buyers_output += f"- <@{buyer_discord_id}> ({count} purchases)\n"

    top_sellers = dataframe["seller_discord_id"].value_counts().head(3)
    top_sellers_output = ""
    for seller_discord_id, count in top_sellers.items():
        top_sellers_output += f"- <@{seller_discord_id}> ({count} sales)\n"

    user_sales_percentage = int(
        ((user_count_buyer_all + user_count_seller_all) / server_count_all) * 100
    )

    # Generate output
    log.debug("Building stats output")
    output = "**Personal Stats**\n"
    output += f"You've made {user_count_buyer_all} purchases and {user_count_seller_all} Sales.\n"
    output += "\n"
    output += f"Of your {user_count_buyer_all} purchases:\n"
    output += (
        f"- {user_count_buyer_unapproved} {_is_or_are(user_count_buyer_unapproved)} unapproved\n"
        if user_count_buyer_unapproved > 0
        else ""
    )
    output += (
        f"- {user_count_buyer_approved} {_is_or_are(user_count_buyer_approved)} approved\n"
        if user_count_buyer_approved > 0
        else ""
    )
    output += (
        f"- {user_count_buyer_delivered} {_is_or_are(user_count_buyer_delivered)} delivered\n"
        if user_count_buyer_delivered > 0
        else ""
    )
    output += (
        f"- {user_count_buyer_paid} {_is_or_are(user_count_buyer_paid)} paid\n"
        if user_count_buyer_paid > 0
        else ""
    )
    output += (
        f"- {user_count_buyer_completed} {_is_or_are(user_count_buyer_completed)} completed\n"
        if user_count_buyer_completed > 0
        else ""
    )
    output += (
        f"- {user_count_buyer_cancelled} {_is_or_are(user_count_buyer_cancelled)} cancelled\n"
        if user_count_buyer_cancelled > 0
        else ""
    )
    output += "\n"
    output += f"Of your {user_count_seller_all} sales:\n"
    output += (
        f"- {user_count_seller_unapproved} {_is_or_are(user_count_seller_unapproved)} unapproved\n"
        if user_count_seller_unapproved > 0
        else ""
    )
    output += (
        f"- {user_count_seller_approved} {_is_or_are(user_count_seller_approved)} approved\n"
        if user_count_seller_approved > 0
        else ""
    )
    output += (
        f"- {user_count_seller_delivered} {_is_or_are(user_count_seller_delivered)} delivered\n"
        if user_count_seller_delivered > 0
        else ""
    )
    output += (
        f"- {user_count_seller_paid} {_is_or_are(user_count_seller_paid)} paid\n"
        if user_count_seller_paid > 0
        else ""
    )
    output += (
        f"- {user_count_seller_completed} {_is_or_are(user_count_seller_completed)} completed\n"
        if user_count_seller_completed > 0
        else ""
    )
    output += (
        f"- {user_count_seller_cancelled} {_is_or_are(user_count_seller_cancelled)} cancelled\n"
        if user_count_seller_cancelled > 0
        else ""
    )
    output += "\n"

    if buyer_has_transactions:
        output += f"Your average purchase price is £{user_average_purchase_price:.2f}, and you've spent a total of £{user_total_purchase_price:.2f}.\n"
        output += f"Your most expensive purchase is *{user_max_purchase_wine_name}* which you bought from <@{user_max_purchase_wine_seller}> for £{user_max_purchase_wine_price:.2f}.\n"

    if seller_has_transactions:
        output += f"Your average sale price is £{user_average_sale_price:.2f}, and you've made a total of £{user_total_sale_price:.2f}.\n"
        output += f"Your most expensive sale is *{user_max_sale_wine_name}* which you sold to <@{user_max_sale_wine_buyer}> for £{user_max_sale_wine_price:.2f}.\n"

    output += "\n"
    output += "**Server Stats**\n"
    output += f"There have been {server_count_all} transactions recorded in the server, with a total value of £{server_total_price:.2f}. You account for {user_sales_percentage}% of transactions in the server!\n"
    output += f"The average price has been £{server_average_price:.2f}.\n"
    output += f"The most expensive sale recorded was *{server_max_wine_name}* from <@{server_max_wine_seller}> to <@{server_max_wine_buyer}> for £{server_max_wine_price:.2f}.\n"
    output += "\n"
    output += "The three users with the most purchases are:\n"
    output += top_buyers_output
    output += "\n"
    output += "The three users with the most sales are:\n"
    output += top_sellers_output
    return output
