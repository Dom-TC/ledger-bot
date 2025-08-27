"""SQLite implementation of MemberStorageABC."""

import logging
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.sql import ColumnElement

from ledger_bot.errors import (
    MemberAlreadyExistsError,
    MemberCreationError,
    MemberQueryError,
)
from ledger_bot.models import Member

from .abstracts import MemberStorageABC

log = logging.getLogger(__name__)


class MemberStorage(MemberStorageABC):
    """SQLite implementation of MemberStorageABC."""

    async def get_member(
        self, record_id: int, session: AsyncSession
    ) -> Optional[Member]:
        log.info(f"Getting member with record_id {record_id}")
        result: Member | None = await session.get(Member, record_id)
        return result

    async def add_member(self, member: Member, session: AsyncSession) -> Member:
        log.info(f"Adding member {member.nickname}({member.discord_id})")
        session.add(member)
        try:
            await session.flush()
            await session.refresh(member)
            log.info(f"Member added with id {member.id}")
            return member

        except IntegrityError as e:
            log.exception(
                f"Adding member {member.username} ({member.discord_id}) raised an IntegrityError"
            )
            await session.rollback()
            raise MemberAlreadyExistsError(member, e)
        except SQLAlchemyError as e:
            log.exception(
                f"Adding member {member.username} ({member.discord_id}) raised an SQLAlchemyError"
            )
            await session.rollback()
            raise MemberCreationError(member, e)

    async def list_members(
        self, *filters: ColumnElement[bool], session: AsyncSession
    ) -> Optional[List[Member]]:
        log.info(f"Listing members that match query {filters}")
        query = select(Member)
        if filters:
            query = query.where(*filters)
        try:
            result = await session.execute(query)
            members = list(result.scalars().all())
            log.info(f"Found {len(members)} members")
            return members if members else None
        except SQLAlchemyError as e:
            log.exception("Database error when listing members")
            raise MemberQueryError("Failed to list members", e)

    async def delete_member(self, member: Member, session: AsyncSession) -> None:
        log.info(
            f"Deleting member id {member.id} ({member.nickname} ({member.discord_id}))"
        )
        await session.delete(member)
        await session.flush()

    async def update_member(
        self, member: Member, session: AsyncSession, fields: Optional[List[str]] = None
    ) -> Member:
        # Attach the member object to the session
        db_member: Member = await session.merge(member)

        if fields:
            # Only update the specified fields
            for field in fields:
                setattr(db_member, field, getattr(member, field))
            log.info(f"Updating member {db_member.id} fields: {fields}")
        else:
            # Full update: merge already updates all fields
            log.info(f"Updating all fields for member {db_member.id}")

        await session.flush()
        await session.refresh(db_member)
        return db_member
