"""The data model for a record in the `bot_messages` table."""

import enum
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event
    from .transaction import Transaction

log = logging.getLogger(__name__)


class BotMessageType(enum.Enum):
    TRANSACTION = "transaction"
    EVENT = "event"


class BotMessage(Base):
    __tablename__ = "bot_messages"
    __table_args__ = (
        CheckConstraint(
            "(transaction_id IS NOT NULL AND event_id IS NULL) OR "
            "(transaction_id IS NULL AND event_id IS NOT NULL)",
            name="exactly_one_type_id",
        ),
    )

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    message_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    channel_id: Mapped[int] = mapped_column(Integer, nullable=False)
    guild_id: Mapped[int] = mapped_column(Integer, nullable=False)

    message_type: Mapped[BotMessageType] = mapped_column(
        Enum(BotMessageType), nullable=False
    )

    # Only one of these will be set, dictated by message_type
    transaction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=True
    )
    event_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("events.id"), nullable=True
    )

    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction", foreign_keys=[transaction_id], back_populates="bot_messages"
    )
    event: Mapped[Optional["Event"]] = relationship(
        "Event", foreign_keys=[event_id], back_populates="bot_messages"
    )
