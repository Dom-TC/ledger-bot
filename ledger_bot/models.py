"""The datamodels for ledger_bot."""
import logging
from typing import Union

from yarl import URL

log = logging.getLogger(__name__)


class Model:
    def __init__(self, **kwargs):
        for attr in self.attributes:
            setattr(self, attr, kwargs.get(attr))

    def __str__(self):
        attrs = ", ".join(f"{attr}={getattr(self, attr)!r}" for attr in self.attributes)
        return f"{self.__class__.__name__}({attrs})"


class Member(Model):
    attributes = [
        "id",
        "row_id",
        "discord_id",
        "username",
        "nickname",
        "sell_transactions",
        "buy_transactions",
        "bot_id",
    ]

    @classmethod
    def from_airtable(cls, data: dict) -> "Member":
        fields = data["fields"]
        return cls(
            id=data["id"],
            row_id=fields.get("row_id"),
            username=fields.get("username"),
            discord_id=fields.get("discord_id"),
            nickname=fields.get("nickname"),
            sell_transactions=fields.get("sell_transactions"),
            buy_transactions=fields.get("buy_transactions"),
            bot_id=fields.get("bot_id"),
        )

    @property
    def display_name(self):
        name = self.nickname if self.nickname else self.username
        return f"{name}"


class Transaction(Model):
    attributes = [
        "id",
        "row_id",
        "seller_id",
        "buyer_id",
        "wine",
        "price",
        "sale_approved",
        "delivered",
        "paid",
        "cancelled",
        "creation_date",
        "approved_date",
        "paid_date",
        "delivered_date",
        "cancelled_date",
        "sale_message_id",
        "bot_message_id",
        "bot_id",
    ]

    @classmethod
    def from_airtable(cls, data: dict) -> "Member":
        fields = data["fields"]
        return cls(
            id=data["id"],
            row_id=fields.get("row_id"),
            seller_id=fields.get("seller_id"),
            buyer_id=fields.get("buyer_id"),
            wine=fields.get("wine"),
            price=fields.get("price"),
            sale_approved=fields.get("sale_approved"),
            delivered=fields.get("delivered"),
            paid=fields.get("paid"),
            cancelled=fields.get("cancelled"),
            creation_date=fields.get("creation_date"),
            approved_date=fields.get("approved_date"),
            paid_date=fields.get("paid_date"),
            delivered_date=fields.get("delivered_date"),
            cancelled_date=fields.get("cancelled_date"),
            sale_message_id=fields.get("sale_message_id"),
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
        if "wine" in fields:
            data["wine"] = self.wine
        if "price" in fields:
            data["price"] = self.price
        if "sale_approved" in fields:
            data["sale_approved"] = self.sale_approved
        if "delivered" in fields:
            data["delivered"] = self.delivered
        if "paid" in fields:
            data["paid"] = self.paid
        if "cancelled" in fields:
            data["cancelled"] = self.cancelled
        if "creation_date" in fields:
            data["creation_date"] = self.creation_date
        if "approved_date" in fields:
            data["approved_date"] = self.approved_date
        if "paid_date" in fields:
            data["paid_date"] = self.paid_date
        if "delivered_date" in fields:
            data["delivered_date"] = self.delivered_date
        if "cancelled_date" in fields:
            data["cancelled_date"] = self.cancelled_date
        if "sale_message_id" in fields:
            data["sale_message_id"] = self.sale_message_id
        if "bot_message_id" in fields:
            data["bot_message_id"] = self.bot_message_id
        if "bot_id" in fields:
            data["bot_id"] = self.bot_id

        return {
            "id": self.id,
            "fields": data,
        }


class AirTableError(Exception):
    def __init__(
        self, url: URL, response_dict: Union[dict, str], *args: object
    ) -> None:
        error_dict: dict = response_dict["error"]
        self.url = url
        if type(error_dict) is dict:
            self.error_type = error_dict.get("type")
            self.error_message = error_dict.get("message")
        else:
            self.error_type = error_dict
            self.error_message = ""
        super().__init__(*args)

    def __repr__(self) -> str:
        return "{class_name}(type:{error_type}, message:'{error_message}', url:{url})".format(
            class_name=self.__class__,
            error_type=self.error_type,
            error_message=self.error_message,
            url=self.url,
        )

    def __str__(self) -> str:
        return "Error from AirTable operation of type '{error_type}', with message:'{error_message}'. Request URL: {url}".format(
            error_type=self.error_type, error_message=self.error_message, url=self.url
        )
