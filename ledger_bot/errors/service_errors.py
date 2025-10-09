"""Errors relating to services."""

from ledger_bot.models import Member, Transaction


class ServiceError(Exception):
    """Base class for all service-related errors."""

    pass


class TransactionServiceError(ServiceError):
    """Base class for all TransactionService errors."""

    pass


class StatsServiceError(ServiceError):
    """Base class for all StatsService errors."""

    pass


class TransactionCancelledError(TransactionServiceError):
    """Transaction already cancelled."""

    def __init__(self, transaction: Transaction, *args: object):
        self.transaction = transaction
        super().__init__(transaction, *args)

    def __str__(self) -> str:
        return f"The transaction({self.transaction.id}) has already been cancelled."


class TransactionApprovedError(TransactionServiceError):
    """Transaction already approved."""

    def __init__(self, transaction: Transaction, *args: object):
        self.transaction = transaction
        super().__init__(transaction, *args)

    def __str__(self) -> str:
        return f"The transaction({self.transaction.id}) has already been approved."


class TransactionInvalidBuyerError(TransactionServiceError):
    """The specified buyer isn't the correct buyer for the transaction."""

    def __init__(self, transaction: Transaction, member: Member, *args: object):
        self.transaction = transaction
        self.member = member
        super().__init__(transaction, *args)

    def __str__(self) -> str:
        return f"The provided buyer ({self.member.id}) isn't the buyer in the transaction ({self.transaction.buyer_id})"


class TransactionInvalidSellerError(TransactionServiceError):
    """The specified seller isn't the correct seller for the transaction."""

    def __init__(self, transaction: Transaction, member: Member, *args: object):
        self.transaction = transaction
        self.member = member
        super().__init__(transaction, *args)

    def __str__(self) -> str:
        return f"The provided seller ({self.member.id}) isn't the seller in the transaction ({self.transaction.buyer_id})"


class TransactionInvalidMemberError(TransactionServiceError):
    """The specified member isn't involved in the transaction."""

    def __init__(self, transaction: Transaction, member: Member, *args: object):
        self.transaction = transaction
        self.member = member
        super().__init__(transaction, *args)

    def __str__(self) -> str:
        return f"The provided member ({self.member.id}) isn't in the transaction ({self.transaction.buyer_id})"


class BotMessageServiceError(ServiceError):
    """Base class for all BotMessageService errors."""

    pass


class BotMessageInvalidTransactionError(BotMessageServiceError):
    """The specified transaction is invalid."""

    def __init__(self, transaction: Transaction, *args: object):
        self.transaction = transaction
        super().__init__(transaction, *args)

    def __str__(self) -> str:
        return f"The specified transaction {self.transaction} is invalid."


class InvalidRoleError(StatsServiceError):
    """THe role provided is invalid."""

    def __init__(self, role: str, *args: object):
        self.role = role
        super().__init__(*args)

    def __str__(self) -> str:
        return f"The provided role ({self.role}) is invalid."
