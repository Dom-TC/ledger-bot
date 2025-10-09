"""The data model for a record in the `wines` table."""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .bot_message import BotMessage
    from .member import Member
    from .reminder import Reminder

log = logging.getLogger(__name__)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (CheckConstraint("price >= 0", name="price_not_negative"),)

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    wine: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), nullable=False
    )
    buyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), nullable=False
    )
    sale_approved: Mapped[Optional[bool]] = mapped_column(Integer, default=0)
    buyer_delivered: Mapped[Optional[bool]] = mapped_column(Integer, default=0)
    seller_delivered: Mapped[Optional[bool]] = mapped_column(Integer, default=0)
    buyer_paid: Mapped[Optional[bool]] = mapped_column(Integer, default=0)
    seller_paid: Mapped[Optional[bool]] = mapped_column(Integer, default=0)
    cancelled: Mapped[Optional[bool]] = mapped_column(Integer, default=0)
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    approved_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bot_id: Mapped[str] = mapped_column(String)

    # Relationships
    seller: Mapped["Member"] = relationship(
        "Member", foreign_keys=[seller_id], back_populates="selling_transactions"
    )
    buyer: Mapped["Member"] = relationship(
        "Member", foreign_keys=[buyer_id], back_populates="buying_transactions"
    )
    bot_messages: Mapped[List["BotMessage"]] = relationship(
        "BotMessage",
        back_populates="transaction",
        foreign_keys="BotMessage.transaction_id",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[List["Reminder"]] = relationship(
        "Reminder",
        back_populates="transaction",
        foreign_keys="Reminder.transaction_id",
        cascade="all, delete-orphan",
    )
