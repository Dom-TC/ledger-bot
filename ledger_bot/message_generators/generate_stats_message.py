"""Generates a message telling a user their stats."""

import logging

from ledger_bot.models import Stats

log = logging.getLogger(__name__)


def _is_or_are(qty: int) -> str:
    """Returns is or are depending on whether qty is > 1."""
    return "are" if qty != 1 else "is"


def _pluralise_word(qty: int, word: str) -> str:
    """Returns a pluralised version of word if needed."""
    return f"{word}s" if qty != 1 else word


def generate_stats_message(stats: Stats) -> str:
    """Generate the message to send one someone uses the stats command."""
    if stats.server is None:
        log.info("No transactions recorded. Can't generate stats.")
        return "No transactions have been recorded. Can't generate stats."

    # Generate output
    log.debug("Building stats output")

    output = ""

    log.debug(f"Purchase: {stats.purchase}")
    log.debug(f"Sale: {stats.sale}")
    log.debug(f"Server: {stats.server}")

    if stats.purchase or stats.sale:
        output += "**Personal Stats**\n"

    if stats.purchase and stats.sale:
        output += f"You've made {stats.purchase.total_count} {_pluralise_word(stats.purchase.total_count, 'purchase')} and {stats.sale.total_count} {_pluralise_word(stats.sale.total_count, 'sale')}.\n"
        output += "\n"
    elif stats.purchase:
        output += f"You've made {stats.purchase.total_count} {_pluralise_word(stats.purchase.total_count, 'purchase')}.\n"
        output += "\n"
    elif stats.sale:
        output += f"You've made {stats.sale.total_count} {_pluralise_word(stats.sale.total_count, 'sale')}.\n"
        output += "\n"

    if stats.purchase:
        output += f"Of your {stats.purchase.total_count} {_pluralise_word(stats.purchase.total_count, 'purchase')}:\n"
        output += (
            f"- {stats.purchase.unapproved} {_is_or_are(stats.purchase.unapproved)} unapproved\n"
            if stats.purchase.unapproved > 0
            else ""
        )
        output += (
            f"- {stats.purchase.approved} {_is_or_are(stats.purchase.approved)} approved\n"
            if stats.purchase.approved > 0
            else ""
        )
        output += (
            f"- {stats.purchase.paid} {_is_or_are(stats.purchase.paid)} paid\n"
            if stats.purchase.paid > 0
            else ""
        )
        output += (
            f"- {stats.purchase.delivered} {_is_or_are(stats.purchase.delivered)} delivered\n"
            if stats.purchase.delivered > 0
            else ""
        )
        output += (
            f"- {stats.purchase.completed} {_is_or_are(stats.purchase.completed)} completed\n"
            if stats.purchase.completed > 0
            else ""
        )
        output += (
            f"- {stats.purchase.cancelled} {_is_or_are(stats.purchase.cancelled)} cancelled\n"
            if stats.purchase.cancelled > 0
            else ""
        )
        output += "\n"

    if stats.sale:
        output += f"Of your {stats.sale.total_count} {_pluralise_word(stats.sale.total_count, 'purchase')}:\n"
        output += (
            f"- {stats.sale.unapproved} {_is_or_are(stats.sale.unapproved)} unapproved\n"
            if stats.sale.unapproved > 0
            else ""
        )
        output += (
            f"- {stats.sale.approved} {_is_or_are(stats.sale.approved)} approved\n"
            if stats.sale.approved > 0
            else ""
        )
        output += (
            f"- {stats.sale.paid} {_is_or_are(stats.sale.paid)} paid\n"
            if stats.sale.paid > 0
            else ""
        )
        output += (
            f"- {stats.sale.delivered} {_is_or_are(stats.sale.delivered)} delivered\n"
            if stats.sale.delivered > 0
            else ""
        )
        output += (
            f"- {stats.sale.completed} {_is_or_are(stats.sale.completed)} completed\n"
            if stats.sale.completed > 0
            else ""
        )
        output += (
            f"- {stats.sale.cancelled} {_is_or_are(stats.sale.cancelled)} cancelled\n"
            if stats.sale.cancelled > 0
            else ""
        )
        output += "\n"

    if stats.purchase:
        output += f"Your average purchase price is £{stats.purchase.avg_price:.2f}, and you've spent a total of £{stats.purchase.total_price:.2f}.\n"
        output += f"Your most expensive purchase is *{stats.purchase.most_expensive_name}* which you bought from <@{stats.purchase.most_expensive_member.discord_id}> for £{stats.purchase.most_expensive_price:.2f}.\n"

    if stats.sale:
        output += f"Your average sale price is £{stats.sale.avg_price:.2f}, and you've made a total of £{stats.sale.total_price:.2f}.\n"
        output += f"Your most expensive sale is *{stats.sale.most_expensive_name}* which you sold to <@{stats.sale.most_expensive_member.discord_id}> for £{stats.sale.most_expensive_price:.2f}.\n"

    if stats.server:
        log.debug(f"Percentage: {stats.user_percentage}")
        log.debug(f"User Total: {stats.user_total}")
        log.debug(
            f"Purchase total: {stats.purchase.total_count if stats.purchase else 'NA'}"
        )
        log.debug(f"Sale total: {stats.sale.total_count if stats.sale else 'NA'}")
        log.debug(f"Server total: {stats.server.total_count if stats.server else 'NA'}")

        output += "\n"
        output += "**Server Stats**\n"
        output += f"There have been {stats.server.total_count} transactions recorded in the server, with a total value of £{stats.server.total_value:.2f}. You account for {stats.user_percentage:.1f}% of transactions in the server!\n"
        output += f"The average price has been £{stats.server.avg_price:.2f}.\n"
        output += f"The most expensive sale recorded was *{stats.server.most_expensive_name}* for £{stats.server.most_expensive_value:.2f}.\n"
        output += "\n"
        output += "The three users with the most purchases are:\n"

        for buyer in stats.server.top_buyers[0:2]:
            output += f"- <@{buyer.discord_id}>\n"
        output += "\n"
        output += "The three users with the most sales are:\n"
        for seller in stats.server.top_sellers[0:2]:
            output += f"- <@{seller.discord_id}>\n"

    return output
