"""The data model for a record in the `reminderrs` table."""

import enum
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .member import Member
    from .transaction import Transaction

log = logging.getLogger(__name__)


class ReminderStatus(enum.Enum):
    APPROVED = "approved"
    CANCELLED = "cancelled"
    DELIVERED = "delivered"
    PAID = "paid"
    COMPLETED = "completed"


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), nullable=False
    )
    transaction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=False
    )
    category: Mapped[Optional[ReminderStatus]] = mapped_column(
        Enum(ReminderStatus), nullable=True
    )
    reminder_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction", foreign_keys=[transaction_id], back_populates="reminders"
    )
    member: Mapped["Member"] = relationship(
        "Member", foreign_keys=[member_id], back_populates="reminders"
    )
