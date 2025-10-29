"""The primary service container."""

from dataclasses import dataclass

from .bot_message_service import BotMessageService
from .currency_service import CurrencyService
from .event_region_service import EventRegionService
from .member_service import MemberService
from .reaction_role_service import ReactionRoleService
from .reminder_service import ReminderService
from .stats_service import StatsService
from .transaction_service import TransactionService


@dataclass
class Service:
    bot_message: BotMessageService
    member: MemberService
    reaction_role: ReactionRoleService
    reminder: ReminderService
    transaction: TransactionService
    stats: StatsService
    currency: CurrencyService
    event_region: EventRegionService
