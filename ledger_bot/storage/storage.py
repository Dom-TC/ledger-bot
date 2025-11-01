"""The primary storage container."""

from dataclasses import dataclass

from .bot_message_storage import BotMessageStorage
from .currency_storage import CurrencyStorage
from .event_member_storage import EventMemberStorage
from .event_region_storage import EventRegionStorage
from .event_storage import EventStorage
from .member_storage import MemberStorage
from .reaction_role_storage import ReactionRoleStorage
from .reminder_storage import ReminderStorage
from .transaction_storage import TransactionStorage


@dataclass
class Storage:
    bot_message: BotMessageStorage
    member: MemberStorage
    reaction_role: ReactionRoleStorage
    reminder: ReminderStorage
    transaction: TransactionStorage
    currency: CurrencyStorage
    event_region: EventRegionStorage
    event: EventStorage
    event_member: EventMemberStorage
