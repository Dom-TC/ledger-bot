"""A service to provide interfacing for StatsService."""

import logging
from collections import Counter
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from ledger_bot.errors import InvalidRoleError
from ledger_bot.models import Member, ServerStats, Stats, Transaction, TransactionStats
from ledger_bot.storage import TransactionStorage

from .service_helpers import ServiceHelpers

log = logging.getLogger(__name__)


class StatsService(ServiceHelpers):
    def __init__(
        self,
        transaction_storage: TransactionStorage,
        bot_id: str,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self.transaction_storage = transaction_storage
        self.bot_id = bot_id

        super().__init__(session_factory)

    async def _build_transaction_stats(
        self,
        user: Member,
        role: str,
        session: AsyncSession | None = None,
    ) -> TransactionStats | None:
        async with self._get_session(session) as session:
            log.debug(f"Building transaction stats for {user.username} as {role}")

            if role != "buyer" and role != "seller":
                log.error(f"Role {role} is invalid. Should be `buyer` or `seller`.")
                raise InvalidRoleError(role)

            unapproved = await self.transaction_storage.get_count_by_status(
                member_id=user.id, role=role, status="unapproved", session=session
            )
            approved = await self.transaction_storage.get_count_by_status(
                member_id=user.id, role=role, status="approved", session=session
            )
            paid = await self.transaction_storage.get_count_by_status(
                member_id=user.id, role=role, status="paid", session=session
            )
            delivered = await self.transaction_storage.get_count_by_status(
                member_id=user.id, role=role, status="delivered", session=session
            )
            completed = await self.transaction_storage.get_count_by_status(
                member_id=user.id, role=role, status="completed", session=session
            )
            cancelled = await self.transaction_storage.get_count_by_status(
                member_id=user.id, role=role, status="cancelled", session=session
            )

            total_count = await self.transaction_storage.get_count_by_status(
                member_id=user.id, role=role, status="all", session=session
            )

            if total_count == 0:
                log.info(f"User has no transactions as {role}")
                return None

            avg_price, total_price = await self.transaction_storage.get_price_stats(
                member_id=user.id, role=role, include_cancelled=True, session=session
            )

            if role == "buyer":
                most_exp = await self.transaction_storage.list_transactions(
                    Transaction.buyer_id == user.id,
                    order_by=Transaction.price.desc(),
                    limit=1,
                    options=[
                        selectinload(Transaction.buyer),
                        selectinload(Transaction.seller),
                    ],
                    session=session,
                )

                if most_exp is None:
                    log.debug("Most_exp is None")
                    return None
                else:
                    most_exp_name = most_exp[0].wine
                    most_exp_member = most_exp[0].seller
                    most_exp_price = most_exp[0].price

            else:
                most_exp = await self.transaction_storage.list_transactions(
                    Transaction.seller_id == user.id,
                    order_by=Transaction.price.desc(),
                    limit=1,
                    options=[
                        selectinload(Transaction.buyer),
                        selectinload(Transaction.seller),
                    ],
                    session=session,
                )

                if most_exp is None:
                    log.debug("Most_exp is None")
                    return None
                else:
                    most_exp_name = most_exp[0].wine
                    most_exp_member = most_exp[0].seller
                    most_exp_price = most_exp[0].price

            return TransactionStats(
                unapproved=unapproved,
                approved=approved,
                paid=paid,
                delivered=delivered,
                completed=completed,
                cancelled=cancelled,
                avg_price=avg_price or 0,
                total_price=total_price or 0,
                total_count=total_count,
                most_expensive_name=most_exp_name,
                most_expensive_member=most_exp_member,
                most_expensive_price=most_exp_price,
            )

    async def _build_server_stats(self, session) -> ServerStats | None:
        """Build the server-wide statistics for all transactions."""
        async with self._get_session(session) as session:
            log.debug("Building server stats")

            all_transactions = await self.transaction_storage.list_transactions(
                session=session,
                options=[
                    selectinload(Transaction.buyer),
                    selectinload(Transaction.seller),
                ],
            )
            if not all_transactions:
                log.info("No transactions found for server stats")
                return None

            total_count = len(all_transactions)
            prices = [t.price for t in all_transactions if t.price is not None]
            total_value = sum(prices)
            avg_price = total_value / len(prices) if prices else 0.0

            # Most expensive transaction
            most_exp_tx = max(all_transactions, key=lambda t: t.price or 0)
            most_expensive_name = most_exp_tx.wine
            most_expensive_value = most_exp_tx.price or 0

            # Count buyers and sellers
            buyer_counter = Counter(t.buyer for t in all_transactions)
            seller_counter = Counter(t.seller for t in all_transactions)

            # Top 3 buyers and sellers
            top_buyers: List[Member] = [b for b, _ in buyer_counter.most_common(3)]
            top_sellers: List[Member] = [s for s, _ in seller_counter.most_common(3)]

            return ServerStats(
                total_count=total_count,
                avg_price=avg_price,
                total_value=total_value,
                most_expensive_name=most_expensive_name,
                most_expensive_value=most_expensive_value,
                top_buyers=top_buyers,
                top_sellers=top_sellers,
            )

    async def get_stats(
        self,
        user: Member,
        session: AsyncSession | None = None,
    ) -> Stats:
        """Get stats for a given user.

        Parameters
        ----------
        user : Member
            The user being looked up
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        Stats
            The Stats object
        """
        log.debug(f"Getting stats for {user.username}")

        async with self._get_session(session) as session:
            purchase = await self._build_transaction_stats(user, "buyer", session)
            sale = await self._build_transaction_stats(user, "seller", session)
            server = await self._build_server_stats(session)

            return Stats(
                purchase=purchase,
                sale=sale,
                server=server,
            )
