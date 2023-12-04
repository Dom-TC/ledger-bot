"""The data model for a record in the `wines` table."""
import logging
from ast import literal_eval
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

from .bot_message import BotMessage
from .member import Member

if TYPE_CHECKING:
    from .reminder import Reminder

log = logging.getLogger(__name__)


@dataclass
class Transaction:
    seller_id: str | Member
    buyer_id: str | Member
    wine: str
    price: float
    record_id: str | None = None
    row_id: str | None = None
    seller_discord_id: int | None = None
    buyer_discord_id: int | None = None
    sale_approved: bool | None = None
    buyer_marked_delivered: bool | None = None
    seller_marked_delivered: bool | None = None
    buyer_marked_paid: bool | None = None
    seller_marked_paid: bool | None = None
    cancelled: bool | None = None
    creation_date: str | None = None
    approved_date: str | None = None
    paid_date: str | None = None
    delivered_date: str | None = None
    cancelled_date: str | None = None
    bot_messages: List[str | BotMessage] | None = None
    reminders: "List[str | Reminder] | None" = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: dict) -> "Transaction":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            seller_id=fields.get("seller_id")[0],
            seller_discord_id=int(fields.get("seller_discord_id")[0]),
            buyer_id=fields.get("buyer_id")[0],
            buyer_discord_id=int(fields.get("buyer_discord_id")[0]),
            wine=fields.get("wine"),
            price=float(fields.get("price")),
            sale_approved=literal_eval(fields.get("sale_approved")),
            buyer_marked_delivered=literal_eval(fields.get("buyer_marked_delivered")),
            seller_marked_delivered=literal_eval(fields.get("seller_marked_delivered")),
            buyer_marked_paid=literal_eval(fields.get("buyer_marked_paid")),
            seller_marked_paid=literal_eval(fields.get("seller_marked_paid")),
            cancelled=literal_eval(fields.get("cancelled")),
            creation_date=fields.get("creation_date"),
            approved_date=fields.get("approved_date"),
            paid_date=fields.get("paid_date"),
            delivered_date=fields.get("delivered_date"),
            cancelled_date=fields.get("cancelled_date"),
            bot_messages=fields.get("bot_messages"),
            reminders=fields.get("reminders"),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields: List | None = None) -> dict:
        fields = (
            fields
            if fields
            else [
                "wine",
                "price",
                "buyer_id",
                "seller_id",
                "sale_approved",
                "buyer_marked_delivered",
                "seller_marked_delivered",
                "buyer_marked_paid",
                "seller_marked_paid",
                "cancelled",
                "creation_date",
                "approved_date",
                "paid_date",
                "delivered_date",
                "cancelled_date",
                "bot_id",
            ]
        )

        data: Dict[str, str | List] = {}

        if "seller_id" in fields:
            data["seller_id"] = [
                self.seller_id.record_id
                if isinstance(self.seller_id, Member)
                else self.seller_id
            ]

        if "buyer_id" in fields:
            data["buyer_id"] = [
                self.buyer_id.record_id
                if isinstance(self.buyer_id, Member)
                else self.buyer_id
            ]

        if "bot_messages" in fields and self.bot_messages is not None:
            data["bot_messages"] = [
                self.bot_messages.record_id
                if isinstance(self.bot_messages, BotMessage)
                else self.bot_messages
            ]

        # For any attribute which is just assigned, without alteration we can list it here and iterate through the list
        # ie. anywhere we would do `data[attr] = self.attr`
        standard_conversions = [
            "wine",
            "price",
            "sale_approved",
            "buyer_marked_delivered",
            "seller_marked_delivered",
            "buyer_marked_paid",
            "seller_marked_paid",
            "cancelled",
            "creation_date",
            "approved_date",
            "paid_date",
            "delivered_date",
            "cancelled_date",
            "bot_id",
        ]
        for attr in standard_conversions:
            if attr in fields:
                data[attr] = str(getattr(self, attr))

        return {
            "id": self.record_id,
            "fields": data,
        }
