"""SQLite implementation of MemberStorageABC."""

import logging
from typing import Dict, List, Optional

from sqlalchemy import Row, case, delete, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import ColumnElement

from ledger_bot.errors import (
    MemberAlreadyExistsError,
    MemberCreationError,
    MemberQueryError,
)
from ledger_bot.models import Member, MemberTransactionSummary, Transaction

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

    async def get_transaction_summary(
        self, member: Member, session: AsyncSession
    ) -> MemberTransactionSummary:
        log.debug(f"Getting transaction summery for {member.username} ({member.id})")

        stmt = select(
            func.sum(case((Transaction.seller_id == member.id, 1), else_=0)).label(
                "sales"
            ),
            func.sum(case((Transaction.buyer_id == member.id, 1), else_=0)).label(
                "purchases"
            ),
            func.sum(case((Transaction.cancelled.is_(True), 1), else_=0)).label(
                "cancelled"
            ),
            func.sum(
                case(
                    (
                        Transaction.buyer_paid.is_(True)
                        & Transaction.seller_paid.is_(True)
                        & Transaction.seller_delivered.is_(True)
                        & Transaction.buyer_delivered.is_(True)
                        & Transaction.cancelled.is_(False),
                        1,
                    ),
                    else_=0,
                )
            ).label("complete"),
            func.sum(
                case(
                    (
                        Transaction.cancelled.is_(False)
                        & (
                            (Transaction.buyer_paid.is_(False))
                            | (Transaction.seller_paid.is_(False))
                            | (Transaction.buyer_delivered.is_(False))
                            | (Transaction.seller_delivered.is_(False))
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("open"),
        ).where(
            (Transaction.seller_id == member.id) | (Transaction.buyer_id == member.id)
        )

        result = await session.execute(stmt)
        row = result.one()

        return MemberTransactionSummary(
            sales_count=row.sales,
            purchases_count=row.purchases,
            completed_count=row.complete,
            cancelled_count=row.cancelled,
            open_count=row.open,
        )
