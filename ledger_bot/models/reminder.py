"""The data model for a record in the `bot_messages` table."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from .member import Member
from .transaction import Transaction

log = logging.getLogger(__name__)


@dataclass
class Reminder:
    date: datetime
    member_id: str | Member
    transaction_id: str | Transaction
    record_id: str | None = None
    row_id: str | None = None
    status: str | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: dict) -> "Reminder":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            date=datetime.strptime(fields.get("date"), "%Y-%m-%dT%H:%M:%S.%f%z"),
            member_id=fields.get("member_id"),
            transaction_id=fields.get("transaction_id"),
            status=fields.get("status"),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields=None) -> dict:
        fields = (
            fields
            if fields
            else [
                "date",
                "member_id",
                "transaction_id",
                "status",
                "bot_id",
            ]
        )

        data: Dict[str, str | List] = {}
        if "date" in fields:
            data["date"] = self.date.isoformat()

        if "member_id" in fields:
            data["member_id"] = [
                self.member_id.record_id
                if isinstance(self.member_id, Member)
                else self.member_id
            ]

        if "transaction_id" in fields:
            data["transaction_id"] = [
                self.transaction_id.record_id
                if isinstance(self.transaction_id, Transaction)
                and self.transaction_id.record_id is not None
                else self.transaction_id
            ]

        if "status" in fields and self.status is not None:
            data["status"] = self.status

        return {
            "id": self.record_id,
            "fields": data,
        }
