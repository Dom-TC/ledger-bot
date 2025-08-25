"""SQLite implementation of MemberStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import ColumnElement

from ledger_bot.models import Member

from .abstracts import MemberStorageABC

log = logging.getLogger(__name__)


class MemberStorage(MemberStorageABC):
    """SQLite implementation of MemberStorageABC."""

    def __init__(self, session_factory: sessionmaker):
        """Initialise MemberStorage.

        Parameters
        ----------
        session_factory : Callable[[], AsyncSession]
            Factory to produce new SQLAlchemy AsyncSession objects.
        """
        self._session_factory = session_factory

    async def get_member(self, record_id: int) -> Optional[Member]:
        async with self._session_factory() as session:
            log.info(f"Getting member with record_id {record_id}")
            result = await session.get(Member, record_id)
            return result

    async def add_member(self, member: Member) -> Member:
        async with self._session_factory() as session:
            log.info(f"Adding member {member.nickname}({member.discord_id})")
            session.add(member)
            await session.commit()
            await session.refresh(member)
            log.info(f"Member added with id {member.id}")
            return member

    async def list_members(
        self, *filters: ColumnElement[bool]
    ) -> Optional[List[Member]]:
        async with self._session_factory() as session:
            log.info(f"Listing members that match query {filters}")
            query = select(Member)
            if filters:
                query = query.where(*filters)
            result = await session.execute(query)
            members = result.scalars().all()
            log.info(f"Found {len(members)} members")
            return members if members else None

    async def delete_member(self, member: Member) -> None:
        async with self._session_factory() as session:
            log.info(
                f"Deleting member id {member.id} ({member.nickname} ({member.discord_id}))"
            )
            await session.delete(member)
            await session.commit()

    async def update_member(
        self, member: Member, fields: Optional[List[str]] = None
    ) -> Member:
        async with self._session_factory() as session:
            # Attach the member object to the session
            db_member = await session.merge(member)

            if fields:
                # Only update the specified fields
                for field in fields:
                    setattr(db_member, field, getattr(member, field))
                log.info(f"Updating member {db_member.id} fields: {fields}")
            else:
                # Full update: merge already updates all fields
                log.info(f"Updating all fields for member {db_member.id}")

            await session.commit()
            await session.refresh(db_member)
            return db_member
