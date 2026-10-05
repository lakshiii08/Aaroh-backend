from typing import Any, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

class AarohAPIException(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

class NotFoundError(AarohAPIException):
    def __init__(self, message: str = "Resource not found", code: str = "RESOURCE_NOT_FOUND", details: Optional[Any] = None):
        super().__init__(message=message, code=code, status_code=status.HTTP_404_NOT_FOUND, details=details)

class UnauthorizedError(AarohAPIException):
    def __init__(self, message: str = "Authentication required", code: str = "UNAUTHORIZED", details: Optional[Any] = None):
        super().__init__(message=message, code=code, status_code=status.HTTP_401_UNAUTHORIZED, details=details)

class ForbiddenError(AarohAPIException):
    def __init__(self, message: str = "Access forbidden", code: str = "FORBIDDEN", details: Optional[Any] = None):
        super().__init__(message=message, code=code, status_code=status.HTTP_403_FORBIDDEN, details=details)

class DuplicateResourceError(AarohAPIException):
    def __init__(self, message: str = "Resource already exists", code: str = "RESOURCE_ALREADY_EXISTS", details: Optional[Any] = None):
        super().__init__(message=message, code=code, status_code=status.HTTP_409_CONFLICT, details=details)

class ValidationError(AarohAPIException):
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR", details: Optional[Any] = None):
        super().__init__(message=message, code=code, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)

class AIProcessingError(AarohAPIException):
    def __init__(self, message: str = "AI processing error", code: str = "AI_PROCESSING_ERROR", details: Optional[Any] = None):
        super().__init__(message=message, code=code, status_code=status.HTTP_502_BAD_GATEWAY, details=details)

def aaroh_exception_handler(request, exc: AarohAPIException) -> JSONResponse:
    content = {
        "success": False,
        "error": {
            "code": exc.code,
            "message": exc.message,
        },
    }
    if exc.details:
        content["error"]["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)
