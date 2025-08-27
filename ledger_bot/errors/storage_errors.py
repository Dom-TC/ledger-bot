"""Errors relating to storage."""

from typing import Optional

from ledger_bot.models import Member


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
