"""The data model for a record in the `bot_messages` table."""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .transaction import Transaction

log = logging.getLogger(__name__)


class BotMessage(Base):
    __tablename__ = "bot_messages"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    message_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    channel_id: Mapped[int] = mapped_column(Integer, nullable=False)
    guild_id: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transactions.id"), nullable=False
    )
    creation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction", foreign_keys=[transaction_id], back_populates="bot_messages"
    )
