"""The data model for a record in the `wines` table."""

import logging
from dataclasses import dataclass

from .bot_message import BotMessage
from .member import Member

log = logging.getLogger(__name__)


@dataclass
class Transaction:
    record_id: str = None
    row_id: str = None
    seller_id: str = None
    seller_discord_id: int = None
    buyer_id: str = None
    buyer_discord_id: int = None
    wine: str = None
    price: float = None
    sale_approved: str = None
    buyer_marked_delivered: str = None
    seller_marked_delivered: str = None
    buyer_marked_paid: str = None
    seller_marked_paid: str = None
    cancelled: str = None
    creation_date: str = None
    approved_date: str = None
    paid_date: str = None
    delivered_date: str = None
    cancelled_date: str = None
    bot_messages: str = None
    bot_id: str = None

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
            sale_approved=fields.get("sale_approved"),
            buyer_marked_delivered=fields.get("buyer_marked_delivered"),
            seller_marked_delivered=fields.get("seller_marked_delivered"),
            buyer_marked_paid=fields.get("buyer_marked_paid"),
            seller_marked_paid=fields.get("seller_marked_paid"),
            cancelled=fields.get("cancelled"),
            creation_date=fields.get("creation_date"),
            approved_date=fields.get("approved_date"),
            paid_date=fields.get("paid_date"),
            delivered_date=fields.get("delivered_date"),
            cancelled_date=fields.get("cancelled_date"),
            bot_messages=fields.get("bot_messages"),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields=None) -> dict:
        fields = fields if fields else self.attributes
        data = {}

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

        if "bot_messages" in fields:
            data["bot_messages"] = [
                self.bot_messages.id
                if isinstance(self.buyer_id, BotMessage)
                else self.bot_messages
            ]

        # For any attribute which is just assigned, without alteration we can list it here and iterate through the list
        # ie. anywhere we would do `data[attr] = self.attr`
        standard_conversions = [
            "wine",
            "price",
            "buyer_discord_id",
            "seller_discord_id",
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
                data[attr] = getattr(self, attr)

        return {
            "id": self.record_id,
            "fields": data,
        }
