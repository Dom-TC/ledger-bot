"""The data model for a record in the `members` table."""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

log = logging.getLogger(__name__)


class Currency(Base):
    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    symbol: Mapped[str] = mapped_column(String)
    rate: Mapped[Optional[float]] = mapped_column(Float)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    bot_id: Mapped[Optional[str]] = mapped_column(String)
