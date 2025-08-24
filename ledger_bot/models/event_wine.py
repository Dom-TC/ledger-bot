"""The EventWine model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .event import Event
from .member import MemberAirtable


class WineCategory(enum.Enum):
    SPARKLING = "sparkling"
    WHITE = "white"
    RED = "red"
    SWEET = "sweet"
    OTHER = "other"


class EventWine(Base):
    __tablename__ = "event_wines"

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), nullable=False)
    wine: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[WineCategory] = mapped_column(Enum(WineCategory), nullable=False)
    date_added: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    bot_id: Mapped[Optional[str]] = mapped_column(String)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="wines")
    member: Mapped["MemberAirtable"] = relationship("Member")
