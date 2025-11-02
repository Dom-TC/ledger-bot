"""Base validation classes and result types.

This module provides the foundational classes for the validation system:
- ValidationResult: Container for validation outcomes
- Validator: Abstract base class for all validators
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class ValidationResult(Generic[T]):
    """Result of a validation operation.

    This class encapsulates the result of a validation, providing both
    success/failure status and either the validated value or error message.

    Attributes
    ----------
    is_valid : bool
        Whether the validation passed
    value : Optional[T]
        The validated and potentially transformed value (None if failed)
    error_message : Optional[str]
        Human-readable error message if validation failed (None if passed)

    Examples
    --------
    >>> result = ValidationResult.success(42)
    >>> result.is_valid
    True
    >>> result.value
    42

    >>> result = ValidationResult.failure("Invalid input")
    >>> result.is_valid
    False
    >>> result.error_message
    'Invalid input'
    """

    is_valid: bool
    value: Optional[T] = None
    error_message: Optional[str] = None

    @classmethod
    def success(cls, value: T) -> "ValidationResult[T]":
        """Create a successful validation result.

        Parameters
        ----------
        value : T
            The validated value

        Returns
        -------
        ValidationResult[T]
            A successful validation result containing the value
        """
        return cls(is_valid=True, value=value, error_message=None)

    @classmethod
    def failure(cls, error_message: str) -> "ValidationResult[T]":
        """Create a failed validation result.

        Parameters
        ----------
        error_message : str
            Human-readable error message explaining the failure

        Returns
        -------
        ValidationResult[T]
            A failed validation result containing the error message
        """
        return cls(is_valid=False, value=None, error_message=error_message)


class Validator(ABC, Generic[T]):
    """Abstract base class for all validators.

    All validators should inherit from this class and implement the validate method.
    Validators can be composed together using CompositeValidator.

    The validation pattern separates validation logic from business logic,
    making code more maintainable and testable.

    Examples
    --------
    >>> class PositiveIntValidator(Validator[int]):
    ...     def validate(self, value):
    ...         try:
    ...             num = int(value)
    ...             if num <= 0:
    ...                 return ValidationResult.failure("Must be positive")
    ...             return ValidationResult.success(num)
    ...         except ValueError:
    ...             return ValidationResult.failure("Must be a valid integer")
    """

    @abstractmethod
    def validate(self, value: Any) -> ValidationResult[T]:
        """Validate a value and return a ValidationResult.

        Parameters
        ----------
        value : Any
            The value to validate

        Returns
        -------
        ValidationResult[T]
            The result of validation including transformed value or error
        """
        pass

    def __call__(self, value: Any) -> ValidationResult[T]:
        """Allow validators to be called directly as functions.

        This enables using validators as callable objects:
        >>> validator = SomeValidator()
        >>> result = validator(input_value)  # Calls validate()
        """
        return self.validate(value)
