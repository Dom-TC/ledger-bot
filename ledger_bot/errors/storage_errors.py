"""Errors relating to storage."""

from typing import Optional

from ledger_bot.models import Currency, Event, EventMember, Member


class StorageError(Exception):
    """Base class for all storage-related errors."""

    pass


class MemberStorageError(StorageError):
    """Base class for all MemberStorage errors."""

    def __init__(self, member: Optional[Member] = None, *args: object):
        self.member = member
        self.discord_id = getattr(member, "discord_id", None) if member else None
        super().__init__(*args)

    def __str__(self) -> str:
        if self.member:
            return f"MemberStorageError: Operation failed for member with discord_id={self.discord_id}"
        return "MemberStorageError: Operation failed."

    def __repr__(self) -> str:
        return f"<MemberStorageError discord_id={self.discord_id}>"


class MemberCreationError(MemberStorageError):
    """Raised when adding a member fails."""

    def __init__(self, member: Member | None = None, *args: object):
        super().__init__(member, *args)

    def __str__(self) -> str:
        return f"Failed to add member with discord_id {self.discord_id}"


class MemberAlreadyExistsError(MemberStorageError):
    """Raised when adding a member fails due to a member already existing."""

    def __init__(self, member: Member | None = None, *args: object):
        super().__init__(member, *args)

    def __str__(self) -> str:
        return f"A member with discord id {self.discord_id} already exists"


class MemberQueryError(MemberStorageError):
    """Raised when listing members fails."""

    def __init__(self, message: str, original_exception: Exception, *args: object):
        super().__init__(None, *args)
        self.original_exception = original_exception

    def __str__(self) -> str:
        return "An exception was raised while listing members"


class CurrencyStorageError(StorageError):
    """Base class for all MemberStorage errors."""

    def __init__(self, currency: Optional[Currency] = None, *args: object):
        self.currency = currency
        self.code = getattr(currency, "code", None) if currency else None
        super().__init__(*args)

    def __str__(self) -> str:
        if self.code:
            return f"MemberStorageError: Operation failed for currency with code={self.code}"
        return "MemberStorageError: Operation failed."

    def __repr__(self) -> str:
        return f"<MemberStorageError code={self.code}>"


class CurrencyAlreadyExistsError(CurrencyStorageError):
    """Raised when adding a currency fails due to a currency already existing."""

    def __init__(self, currency: Currency | None = None, *args: object):
        super().__init__(currency, *args)

    def __str__(self) -> str:
        return f"A currency with code {self.code} already exists"


class CurrencyCreationError(CurrencyStorageError):
    """Raised when adding a currency fails."""

    def __init__(self, currency: Currency | None = None, *args: object):
        super().__init__(currency, *args)

    def __str__(self) -> str:
        return f"Failed to add currency {self.code}"


class CurrencyQueryError(CurrencyStorageError):
    """Raised when listing currencies fails."""

    def __init__(self, message: str, original_exception: Exception, *args: object):
        super().__init__(None, *args)
        self.original_exception = original_exception

    def __str__(self) -> str:
        return "An exception was raised while listing currencies"


class EventStorageError(StorageError):
    """Base class for all EventStorage errors."""

    def __init__(self, event: Optional[Event] = None, *args: object):
        self.event = event
        self.event_id = getattr(event, "id", None) if event else None
        self.event_name = getattr(event, "event_name", None) if event else None
        super().__init__(*args)

    def __str__(self) -> str:
        if self.event:
            return f"EventStorageError: Operation failed for event with id={self.event_id}, name={self.event_name}"
        return "EventStorageError: Operation failed."

    def __repr__(self) -> str:
        return f"<EventStorageError id={self.event_id} name={self.event_name}>"


class EventCreationError(EventStorageError):
    """Raised when adding an event fails."""

    def __init__(self, event: Event | None = None, *args: object):
        super().__init__(event, *args)

    def __str__(self) -> str:
        return f"Failed to add event {self.event_name}"


class EventAlreadyExistsError(EventStorageError):
    """Raised when adding an event fails due to an event already existing."""

    def __init__(self, event: Event | None = None, *args: object):
        super().__init__(event, *args)

    def __str__(self) -> str:
        return f"An event with id {self.event_id} already exists"


class EventQueryError(EventStorageError):
    """Raised when listing events fails."""

    def __init__(self, message: str, original_exception: Exception, *args: object):
        super().__init__(None, *args)
        self.original_exception = original_exception

    def __str__(self) -> str:
        return "An exception was raised while listing events"


class EventChannelError(EventStorageError):
    """Raised when creating or managing an event channel fails."""

    def __init__(self, event: Event | None = None, message: str = "", *args: object):
        super().__init__(event, *args)
        self.message = message

    def __str__(self) -> str:
        if self.message:
            return (
                f"Failed to create channel for event {self.event_name}: {self.message}"
            )
        return f"Failed to create channel for event {self.event_name}"


class EventMemberStorageError(StorageError):
    """Base class for all EventMemberStorage errors."""

    def __init__(self, event_member: Optional[EventMember] = None, *args: object):
        self.event_member = event_member
        self.event_member_id = (
            getattr(event_member, "id", None) if event_member else None
        )
        self.event_id = (
            getattr(event_member, "event_id", None) if event_member else None
        )
        self.member_id = (
            getattr(event_member, "member_id", None) if event_member else None
        )
        super().__init__(*args)

    def __str__(self) -> str:
        if self.event_member:
            return f"EventMemberStorageError: Operation failed for event member with id={self.event_member_id}, event_id={self.event_id}, member_id={self.member_id}"
        return "EventMemberStorageError: Operation failed."

    def __repr__(self) -> str:
        return f"<EventMemberStorageError id={self.event_member_id} event_id={self.event_id} member_id={self.member_id}>"


class EventMemberCreationError(EventMemberStorageError):
    """Raised when adding an event member fails."""

    def __init__(self, event_member: EventMember | None = None, *args: object):
        super().__init__(event_member, *args)

    def __str__(self) -> str:
        return f"Failed to add event member for event_id {self.event_id}, member_id {self.member_id}"


class EventMemberAlreadyExistsError(EventMemberStorageError):
    """Raised when adding an event member fails due to a member already being associated with the event."""

    def __init__(self, event_member: EventMember | None = None, *args: object):
        super().__init__(event_member, *args)

    def __str__(self) -> str:
        return f"An event member for event_id {self.event_id} and member_id {self.member_id} already exists"


class EventMemberQueryError(EventMemberStorageError):
    """Raised when listing event members fails."""

    def __init__(self, message: str, original_exception: Exception, *args: object):
        super().__init__(None, *args)
        self.original_exception = original_exception

    def __str__(self) -> str:
        return "An exception was raised while listing event members"
