"""The Member Transaction Summary."""

from dataclasses import dataclass


@dataclass(slots=True)
class MemberTransactionSummary:
    sales_count: int
    purchases_count: int
    completed_count: int
    cancelled_count: int
    open_count: int
