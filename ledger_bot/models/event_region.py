"""The data model for a record in the `event_regions` table."""

import logging
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event

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
    events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="region",
        foreign_keys="Event.region_id",
        cascade="all, delete-orphan",
    )
