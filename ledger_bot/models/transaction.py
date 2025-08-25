"""The data model for a record in the `wines` table."""
import logging
from ast import literal_eval
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

from .bot_message import BotMessageAirtable
from .member import MemberAirtable

if TYPE_CHECKING:
    from .reminder import ReminderAirtable

log = logging.getLogger(__name__)


@dataclass
class TransactionAirtable:
    seller_id: str | MemberAirtable
    buyer_id: str | MemberAirtable
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
    bot_messages: List[str | BotMessageAirtable] | None = None
    reminders: "List[str | ReminderAirtable] | None" = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "TransactionAirtable":
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
            sale_approved=fields.get("sale_approved", False),
            buyer_marked_delivered=fields.get("buyer_marked_delivered", False),
            seller_marked_delivered=fields.get("seller_marked_delivered", False),
            buyer_marked_paid=fields.get("buyer_marked_paid", False),
            seller_marked_paid=fields.get("seller_marked_paid", False),
            cancelled=fields.get("cancelled", False),
            creation_date=fields.get("creation_date"),
            approved_date=fields.get("approved_date"),
            paid_date=fields.get("paid_date"),
            delivered_date=fields.get("delivered_date"),
            cancelled_date=fields.get("cancelled_date"),
            bot_messages=fields.get("bot_messages"),
            reminders=fields.get("reminders"),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields: List[str] | None = None) -> Dict[str, Any]:
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

        data: Dict[str, str | List[str]] = {}

        if "seller_id" in fields:
            data["seller_id"] = [
                str(self.seller_id.record_id)
                if isinstance(self.seller_id, MemberAirtable)
                else self.seller_id
            ]

        if "buyer_id" in fields:
            data["buyer_id"] = [
                str(self.buyer_id.record_id)
                if isinstance(self.buyer_id, MemberAirtable)
                else self.buyer_id
            ]

        if "bot_messages" in fields and self.bot_messages is not None:
            bot_message_list = []
            for bot_message in self.bot_messages:
                bot_message_list.append(
                    bot_message.record_id
                    if isinstance(bot_message, BotMessageAirtable)
                    else bot_message
                )
            data["bot_messages"] = bot_message_list

        if "reminders" in fields and self.reminders is not None:
            reminder_list = []
            for reminder in self.reminders:
                reminder_list.append(
                    str(reminder.record_id)
                    if isinstance(reminder, ReminderAirtable)
                    else reminder
                )
            data["reminders"] = reminder_list

        # For any attribute which is just assigned, without alteration we can list it here and iterate through the list
        # ie. anywhere we would do `data[attr] = self.attr`
        str_conversions = [
            "wine",
            "creation_date",
            "approved_date",
            "paid_date",
            "delivered_date",
            "cancelled_date",
            "bot_id",
        ]
        for attr in str_conversions:
            if attr in fields:
                data[attr] = str(getattr(self, attr))

        bare_conversions = [
            "price",
            "sale_approved",
            "buyer_marked_delivered",
            "seller_marked_delivered",
            "buyer_marked_paid",
            "seller_marked_paid",
            "cancelled",
        ]
        for attr in bare_conversions:
            if attr in fields:
                data[attr] = getattr(self, attr)

        return {
            "id": self.record_id,
            "fields": data,
        }
