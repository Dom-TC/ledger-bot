"""Additional exceptions."""

from .service_errors import (
    BotMessageInvalidTransactionError,
    BotMessageServiceError,
    InvalidRoleError,
    StatsServiceError,
    TransactionApprovedError,
    TransactionCancelledError,
    TransactionInvalidBuyerError,
    TransactionInvalidMemberError,
    TransactionInvalidSellerError,
    TransactionServiceError,
)
from .signal_halt_error import SignalHaltError
from .storage_errors import (
    CurrencyAlreadyExistsError,
    CurrencyCreationError,
    CurrencyQueryError,
    CurrencyStorageError,
    MemberAlreadyExistsError,
    MemberCreationError,
    MemberQueryError,
    MemberStorageError,
)

__all__ = [
    "SignalHaltError",
    "MemberAlreadyExistsError",
    "MemberCreationError",
    "MemberQueryError",
    "MemberStorageError",
    "TransactionCancelledError",
    "TransactionServiceError",
    "TransactionInvalidBuyerError",
    "TransactionInvalidSellerError",
    "TransactionApprovedError",
    "TransactionInvalidMemberError",
    "BotMessageServiceError",
    "BotMessageInvalidTransactionError",
    "StatsServiceError",
    "InvalidRoleError",
    "CurrencyStorageError",
    "CurrencyAlreadyExistsError",
    "CurrencyCreationError",
    "CurrencyQueryError",
]
