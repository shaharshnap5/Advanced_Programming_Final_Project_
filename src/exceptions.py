"""
Custom exception classes for application-wide error handling.
Maps business logic errors to appropriate HTTP status codes.
"""


class AppException(Exception):
    """Base exception for all application exceptions."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ValidationException(AppException):
    """
    Raised when input validation fails.
    Maps to HTTP 400 Bad Request.
    """
    pass


class NotFoundException(AppException):
    """
    Raised when a requested entity is not found.
    Maps to HTTP 404 Not Found.
    """
    pass


class ConflictException(AppException):
    """
    Raised when there's a conflicting state (e.g., user already on active ride).
    Maps to HTTP 409 Conflict.
    """
    pass
