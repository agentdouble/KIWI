from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        logger.error(f"AppException: {status_code} - {detail}")


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found: {identifier}"
        )


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class BadRequestError(AppException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ConflictError(AppException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class InternalServerError(AppException):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ValidationError(BadRequestError):
    def __init__(self, field: str, message: str):
        super().__init__(detail=f"Validation error on {field}: {message}")


class DatabaseError(InternalServerError):
    def __init__(self, operation: str, error: Exception):
        logger.error(f"Database error during {operation}: {str(error)}", exc_info=True)
        super().__init__(detail=f"Database error during {operation}")


class ExternalServiceError(InternalServerError):
    def __init__(self, service: str, error: Exception):
        logger.error(f"External service error ({service}): {str(error)}", exc_info=True)
        super().__init__(detail=f"External service error: {service}")


class FileProcessingError(InternalServerError):
    def __init__(self, filename: str, error: Exception):
        logger.error(f"File processing error ({filename}): {str(error)}", exc_info=True)
        super().__init__(detail=f"Error processing file: {filename}")