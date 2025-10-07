"""The stats object."""

from dataclasses import dataclass

from .member import Member


@dataclass(slots=True)
class TransactionStats:
    unapproved: int
    approved: int
    paid: int
    delivered: int
    completed: int
    cancelled: int

    avg_price: float
    total_price: float
    total_count: int

    most_expensive_name: str
    most_expensive_member: Member
    most_expensive_price: float


@dataclass(slots=True)
class ServerStats:
    total_count: int
    total_value: float
    avg_price: float
    most_expensive_name: str
    most_expensive_value: float
    top_buyers: list[Member]
    top_sellers: list[Member]


@dataclass(slots=True)
class Stats:
    purchase: TransactionStats | None
    sale: TransactionStats | None
    server: ServerStats | None

    @property
    def user_total(self):
        purchase_total = self.purchase.total_count if self.purchase else 0
        sale_total = self.sale.total_count if self.sale else 0

        return purchase_total + sale_total

    @property
    def user_percentage(self):
        if (self.purchase or self.sale) and self.server:
            percentage = (self.user_total / self.server.total_count) * 100
            return percentage
        else:
            return None
