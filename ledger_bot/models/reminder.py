"""The data model for a record in the `bot_messages` table."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from .member import MemberAirtable
from .transaction import Transaction

log = logging.getLogger(__name__)


@dataclass
class Reminder:
    date: datetime
    member_id: str | MemberAirtable
    transaction_id: str | Transaction
    record_id: str | None = None
    row_id: str | None = None
    status: str | None = None
    bot_id: str | None = None

    @classmethod
    def from_airtable(cls, data: Dict[str, Any]) -> "Reminder":
        fields = data["fields"]
        return cls(
            record_id=data["id"],
            row_id=fields.get("row_id"),
            date=datetime.strptime(fields.get("date"), "%Y-%m-%dT%H:%M:%S.%f%z"),
            member_id=fields.get("member_id")[0],
            transaction_id=fields.get("transaction_id")[0],
            status=fields.get("status"),
            bot_id=fields.get("bot_id"),
        )

    def to_airtable(self, fields: List[str] | None = None) -> Dict[str, Any]:
        fields = (
            fields
            if fields
            else [
                "date",
                "member_id",
                "transaction_id",
                "status",
                "row_id",
                "bot_id",
            ]
        )

        data: Dict[str, str | List[str]] = {}
        if "date" in fields:
            data["date"] = self.date.isoformat()

        if "member_id" in fields:
            data["member_id"] = [
                str(self.member_id.record_id)
                if isinstance(self.member_id, MemberAirtable)
                else self.member_id
            ]

        if "transaction_id" in fields:
            data["transaction_id"] = [
                str(self.transaction_id.record_id)
                if isinstance(self.transaction_id, Transaction)
                else self.transaction_id
            ]

        if "row_id" in fields and self.row_id is not None:
            data["row_id"] = self.row_id

        if "status" in fields and self.status is not None:
            data["status"] = self.status

        if "bot_id" in fields and self.bot_id is not None:
            data["bot_id"] = self.bot_id

        return {
            "id": self.record_id,
            "fields": data,
        }
