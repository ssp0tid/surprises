"""Custom exceptions for Habitbeat."""


class HabitbeatError(Exception):
    status_code = 500
    error_code = "INTERNAL_ERROR"

    def __init__(self, message=None, details=None):
        super().__init__(message)
        self.message = message or self.__class__.__name__
        self.details = details or []


class ValidationError(HabitbeatError):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class NotFoundError(HabitbeatError):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"


class AuthenticationError(HabitbeatError):
    status_code = 401
    error_code = "AUTHENTICATION_REQUIRED"


class PermissionError(HabitbeatError):
    status_code = 403
    error_code = "PERMISSION_DENIED"


class DuplicateError(HabitbeatError):
    status_code = 409
    error_code = "DUPLICATE_RESOURCE"
