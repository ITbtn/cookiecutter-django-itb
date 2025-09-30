import logging

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError, PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    ValidationError,
    PermissionDenied as DRFPermissionDenied,
)
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class BaseException(Exception):
    """
    Base exception class that standardizes error responses across the API.
    """
    code = "INTERNAL_ERROR"
    error_details = {}
    errors = None
    message = "An unexpected error occurred."
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message=None,
        context=None,
        errors=None,
        code=None,
        error_details=None,
        status_code=None,
        *args,
        **kwargs
    ):
        self.message = message or self.message
        self.context = context or {}
        self.errors = errors or self.errors
        self.code = code or self.code
        self.error_details = error_details or self.error_details or {}
        self.status_code = status_code or self.status_code

        # Update context with any additional kwargs
        if kwargs:
            self.context.update(kwargs)

        # Format message with kwargs if provided
        if self.context and self.message:
            try:
                self.message = self.message.format(**self.context)
            except KeyError:
                logger.error("Error formatting exception message with context: %s", self.context)
                pass  # Silently ignore formatting errors

        super().__init__(self.message)

    def __str__(self) -> str:
        return str(self.message)

    def to_dict(self):
        """Convert exception to a standardized dict for API responses."""
        return {
            "code": self.code.upper() if self.code else "INTERNAL_ERROR",
            "message": str(self.message),
            "details": self.error_details,
            "errors": self.errors or {},
        }


class BadRequestException(BaseException):
    code = "BAD_REQUEST"
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundException(BaseException):
    code = "NOT_FOUND"
    message = "Resource not found"
    status_code = status.HTTP_404_NOT_FOUND


class InvalidInputException(BadRequestException):
    code = "INVALID_INPUT"
    message = "Invalid input data"


class UnauthorizedException(BaseException):
    code = "UNAUTHORIZED"
    message = "Authentication required"
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenException(BaseException):
    code = "FORBIDDEN"
    message = "Permission denied"
    status_code = status.HTTP_403_FORBIDDEN


class MethodNotAllowedException(BaseException):
    code = "METHOD_NOT_ALLOWED"
    message = "Method not allowed"
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED


class TimeoutException(BaseException):
    code = "REQUEST_TIMEOUT"
    message = "Request timed out"
    status_code = status.HTTP_408_REQUEST_TIMEOUT


class ServerErrorException(BaseException):
    code = "INTERNAL_SERVER_ERROR"
    message = "Internal server error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ValidationException(BadRequestException):
    code = "VALIDATION_ERROR"
    message = "Validation failed"


class IntegrityErrorException(BadRequestException):
    code = "INTEGRITY_ERROR"
    message = "Database integrity constraint violated."
    status_code = status.HTTP_400_BAD_REQUEST


def format_validation_errors(errors):
    """
    Format validation errors consistently.

    Handles nested errors, list errors, and ensures all error messages are strings.
    """
    def _format_messages(messages):
        if isinstance(messages, dict):
            return {k: _format_messages(v) for k, v in messages.items()}
        elif isinstance(messages, list):
            # Handle lists of errors, which could be strings, dicts, or other objects
            return [
                _format_messages(item) if isinstance(item, (dict, list)) 
                else str(item) for item in messages
            ]
        else:
            # Convert any other type to string
            return str(messages)

    return _format_messages(errors)


def exception_handler(exc, context=None):
    """
    Global exception handler that converts all exceptions into a standardized error response.

    Handles custom, DRF, Django, and built-in exceptions, standardizing them into a single pattern.
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message",
            "details": {},  # Optional additional context
            "errors": {}    # Field-specific errors for validation failures
        }
    }
    """
    # Convert common Django/DRF exceptions to our base exceptions
    if isinstance(exc, Http404):
        exc = NotFoundException(message="Resource not found")
    elif isinstance(exc, NotFound):
        exc = NotFoundException(message=str(exc) if str(exc) else "Resource not found")
    elif isinstance(exc, ValidationError):
        # Convert DRF ValidationError to ValidationException
        exc = ValidationException(errors=format_validation_errors(exc.detail))
    elif isinstance(exc, DjangoValidationError):
        # Convert Django ValidationError to ValidationException
        if hasattr(exc, 'message_dict'):
            errors = exc.message_dict
        else:
            errors = {'non_field_errors': exc.messages if hasattr(exc, 'messages') else [str(exc)]}
        exc = ValidationException(errors=format_validation_errors(errors))
    elif isinstance(exc, (PermissionDenied, DRFPermissionDenied)):
        exc = ForbiddenException(message=str(exc) if str(exc) else "Permission denied")
    elif isinstance(exc, NotAuthenticated):
        exc = UnauthorizedException()
    elif isinstance(exc, AuthenticationFailed):
        exc = UnauthorizedException(message=str(exc))
    elif isinstance(exc, MethodNotAllowed):
        exc = MethodNotAllowedException()


    # For unexpected exceptions, log it but don't expose details
    elif not isinstance(exc, (APIException, BaseException)):
        logger.exception("Unhandled exception: %s", exc)
        exc = ServerErrorException(
            message="An internal error occurred.",
            error_details={"exception_type": exc.__class__.__name__, "original_error": str(exc)} if settings.DEBUG else {}
        )

    # Convert to standardized format
    if hasattr(exc, 'to_dict'):
        error_dict = exc.to_dict()
    else:
        # Fallback for any exception that somehow gets here without being handled
        error_dict = {
            "code": getattr(exc, "code", "UNKNOWN_ERROR").upper(),
            "message": str(exc) or "An unexpected error occurred",
            "details": getattr(exc, "error_details", {}),
            "errors": getattr(exc, "errors", []),
        }

    # Ensure code is uppercase and consistent
    error_dict["code"] = error_dict["code"].upper()

    # Return the error wrapped in an "error" object for consistent frontend handling
    return Response(
        {"error": error_dict},
        status=getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    )
