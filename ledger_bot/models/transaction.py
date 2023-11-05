"""The data model for a record in the `wines` table."""

import logging

from .member import Member
from .model import Model

log = logging.getLogger(__name__)


class Transaction(Model):
    attributes = [
        "id",
        "row_id",
        "seller_id",
        "buyer_id",
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
        "guild_id",
        "channel_id",
        "bot_message_id",
        "bot_id",
    ]

    @classmethod
    def from_airtable(cls, data: dict) -> "Transaction":
        fields = data["fields"]
        return cls(
            id=data["id"],
            row_id=fields.get("row_id"),
            seller_id=fields.get("seller_id")[0],
            buyer_id=fields.get("buyer_id")[0],
            wine=fields.get("wine"),
            price=fields.get("price"),
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
            guild_id=fields.get("guild_id"),
            channel_id=fields.get("channel_id"),
            bot_message_id=fields.get("bot_message_id"),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields=None) -> dict:
        fields = fields if fields else self.attributes
        data = {}

        if "seller_id" in fields:
            data["seller_id"] = [
                self.seller_id.id
                if isinstance(self.seller_id, Member)
                else self.seller_id
            ]
        if "buyer_id" in fields:
            data["buyer_id"] = [
                self.buyer_id.id if isinstance(self.buyer_id, Member) else self.buyer_id
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
            "guild_id",
            "channel_id",
            "bot_message_id",
            "bot_id",
        ]
        for attr in standard_conversions:
            if attr in fields:
                data[attr] = getattr(self, attr)

        return {
            "id": self.id,
            "fields": data,
        }
