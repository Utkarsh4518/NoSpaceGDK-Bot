"""Exceptions specific to the validation schemas layer."""

from utils.exceptions import NoSpaceFGKError


class ValidationError(NoSpaceFGKError):
    """Raised when validating a dictionary payload against a schema fails."""
