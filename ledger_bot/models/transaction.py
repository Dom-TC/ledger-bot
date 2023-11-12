"""The data model for a record in the `wines` table."""

import logging
from dataclasses import dataclass
from typing import Optional, Union

from .bot_message import BotMessage
from .member import Member

log = logging.getLogger(__name__)


@dataclass
class Transaction:
    record_id: Optional[str] = None
    row_id: Optional[str] = None
    seller_id: Optional[str] = None
    seller_discord_id: Optional[int] = None
    buyer_id: Optional[str] = None
    buyer_discord_id: Optional[int] = None
    wine: Optional[str] = None
    price: Optional[float] = None
    sale_approved: Optional[bool] = None
    buyer_marked_delivered: Optional[bool] = None
    seller_marked_delivered: Optional[bool] = None
    buyer_marked_paid: Optional[bool] = None
    seller_marked_paid: Optional[bool] = None
    cancelled: Optional[bool] = None
    creation_date: Optional[str] = None
    approved_date: Optional[str] = None
    paid_date: Optional[str] = None
    delivered_date: Optional[str] = None
    cancelled_date: Optional[str] = None
    bot_messages: Optional[BotMessage] = None
    bot_id: Optional[str] = None

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
        fields = (
            fields
            if fields
            else [
                "wine",
                "price",
                "buyer_id",
                "buyer_discord_id",
                "seller_id",
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
                "bot_messages",
            ]
        )
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
                self.bot_messages.record_id
                if isinstance(self.bot_messages, BotMessage)
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
