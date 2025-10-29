"""The data model for a record in the `event_regions` table."""

import logging
from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

log = logging.getLogger(__name__)


class EventRegion(Base):
    __tablename__ = "event_regions"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    region_name: Mapped[str] = mapped_column(String, unique=True)
    new_event_category: Mapped[int] = mapped_column(Integer)
    event_post_channel: Mapped[int] = mapped_column(Integer)
    bot_id: Mapped[Optional[str]] = mapped_column(String)
