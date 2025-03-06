"""
FMG-Batch exceptions.

This module provides custom exceptions for the FMG-Batch client.
"""


class FortiManagerError(Exception):
    """Base exception for FortiManager API errors."""

    pass


class FortiManagerAuthError(FortiManagerError):
    """Exception raised for authentication errors."""

    pass


class FortiManagerAPIError(FortiManagerError):
    """Exception raised for API errors."""

    pass


class FortiManagerConfigError(FortiManagerError):
    """Exception raised for configuration errors."""

    pass


class FortiManagerFileError(FortiManagerError):
    """Exception raised for file-related errors."""

    pass
