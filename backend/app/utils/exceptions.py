from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, details: Optional[Any] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(
        self, message: str = "Resource not found", details: Optional[Any] = None
    ):
        super().__init__(404, "NOT_FOUND", message, details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None):
        super().__init__(401, "UNAUTHORIZED", message, details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None):
        super().__init__(403, "FORBIDDEN", message, details)


class ValidationException(AppException):
    def __init__(
        self, message: str = "Validation error", details: Optional[Any] = None
    ):
        super().__init__(400, "VALIDATION_ERROR", message, details)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", details: Optional[Any] = None):
        super().__init__(409, "CONFLICT", message, details)


class RateLimitException(AppException):
    def __init__(
        self, message: str = "Too many requests", details: Optional[Any] = None
    ):
        super().__init__(429, "RATE_LIMIT_EXCEEDED", message, details)
