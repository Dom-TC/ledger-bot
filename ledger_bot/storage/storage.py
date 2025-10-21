"""The primary storage container."""

from dataclasses import dataclass

from .bot_message_storage import BotMessageStorage
from .currency_storage import CurrencyStorage
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
