"""The EventWine model."""

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .event import Event
    from .event_member import EventMember


class WineCategory(enum.Enum):
    SPARKLING = "sparkling"
    WHITE = "white"
    RED = "red"
    SWEET = "sweet"
    OTHER = "other"


class WineSize(enum.Enum):
    HALF = "37.5"
    FIFTYCL = "50"
    BOTTLE = "75"
    MAG = "150"
    DMAG = "300"


class EventWine(Base):
    __tablename__ = "event_wines"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    event_member_id: Mapped[int] = mapped_column(
        ForeignKey("event_members.id"), nullable=False
    )
    wine: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[WineSize] = mapped_column(
        Enum(WineSize), nullable=False, default=WineSize.BOTTLE
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    category: Mapped[WineCategory] = mapped_column(Enum(WineCategory), nullable=False)
    date_added: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    event: Mapped["Event"] = relationship(
        "Event", back_populates="wines", lazy="joined"
    )
    event_member: Mapped["EventMember"] = relationship(
        "EventMember", back_populates="wines", lazy="joined"
    )
