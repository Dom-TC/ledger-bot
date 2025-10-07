"""The data model for a record in the `reaction_roles` table."""

import logging
from typing import Optional

from sqlalchemy import Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

log = logging.getLogger(__name__)


class ReactionRole(Base):
    __tablename__ = "reaction_roles"
    __table_args__ = (
        UniqueConstraint(
            "server_id",
            "message_id",
            "reaction_name",
            name="uq_server_message_reaction",
        ),
        Index(
            "ix_server_message_reaction",
            "server_id",
            "message_id",
            "reaction_name",
        ),
    )

    id: Mapped[int] = mapped_column(  # noqa: A003
        Integer, primary_key=True, autoincrement=True
    )
    server_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reaction_name: Mapped[str] = mapped_column(String, nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False)
    role_name: Mapped[str] = mapped_column(String, nullable=False)
    reaction_bytecode: Mapped[str] = mapped_column(String, nullable=False)
    bot_id: Mapped[Optional[str]] = mapped_column(String)
