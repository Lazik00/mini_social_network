from typing import Any


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)


class BadRequestError(AppException):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(400, message, details)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(401, message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(403, message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(404, message)


class ConflictError(AppException):
    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(409, message, details)


class TooManyRequestsError(AppException):
    def __init__(self, message: str = "Too many requests") -> None:
        super().__init__(429, message)
