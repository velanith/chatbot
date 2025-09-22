"""Error handling middleware for consistent error responses."""

import logging
import traceback
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from src.domain.exceptions import (
    DomainError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError,
    ChatError,
    SessionError,
    ServiceError,
    ErrorCode
)
from src.presentation.schemas.common_schemas import (
    ErrorResponse,
    ErrorDetail,
    ErrorType
)

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and returning consistent error responses."""
    
    def __init__(self, app, debug: bool = False):
        """Initialize error handling middleware.
        
        Args:
            app: FastAPI application
            debug: Whether to include debug information in responses
        """
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next):
        """Process request and handle any exceptions."""
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            return await self._handle_exception(request, exc, request_id)
    
    async def _handle_exception(
        self,
        request: Request,
        exc: Exception,
        request_id: str
    ) -> JSONResponse:
        """Handle exception and return appropriate JSON response.
        
        Args:
            request: FastAPI request
            exc: Exception that occurred
            request_id: Request tracking ID
            
        Returns:
            JSON response with error details
        """
        # Log the exception
        logger.error(
            f"Request {request_id} failed: {type(exc).__name__}: {str(exc)}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)
            },
            exc_info=self.debug
        )
        
        # Handle different exception types
        if isinstance(exc, HTTPException):
            return await self._handle_http_exception(exc, request_id)
        elif isinstance(exc, RequestValidationError):
            return await self._handle_validation_error(exc, request_id)
        elif isinstance(exc, DomainError):
            return await self._handle_domain_error(exc, request_id)
        else:
            return await self._handle_unexpected_error(exc, request_id)
    
    async def _handle_http_exception(
        self,
        exc: HTTPException,
        request_id: str
    ) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_type = self._get_error_type_from_status(exc.status_code)
        
        error_response = ErrorResponse(
            error_type=error_type,
            message=exc.detail if isinstance(exc.detail, str) else "HTTP error occurred",
            request_id=request_id,
            debug_info={"status_code": exc.status_code} if self.debug else None
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    async def _handle_validation_error(
        self,
        exc: RequestValidationError,
        request_id: str
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_details = []
        
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            error_detail = ErrorDetail(
                field=field_path,
                message=error["msg"],
                code=error["type"]
            )
            error_details.append(error_detail)
        
        error_response = ErrorResponse(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Request validation failed",
            details=error_details,
            request_id=request_id,
            debug_info={"raw_errors": exc.errors()} if self.debug else None
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(mode='json')
        )
    
    async def _handle_domain_error(
        self,
        exc: DomainError,
        request_id: str
    ) -> JSONResponse:
        """Handle domain-specific errors."""
        # Map domain error codes to HTTP status codes
        status_code = self._get_status_code_from_error_code(exc.error_code)
        error_type = self._get_error_type_from_error_code(exc.error_code)
        
        # Create error details if available
        error_details = []
        if hasattr(exc, 'field') and exc.field:
            error_detail = ErrorDetail(
                field=exc.field,
                message=exc.message,
                code=exc.error_code.value
            )
            error_details.append(error_detail)
        
        # Add debug information
        debug_info = None
        if self.debug:
            debug_info = {
                "exception_type": type(exc).__name__,
                "error_code": exc.error_code.value,
                "details": exc.details,
                "cause": str(exc.cause) if exc.cause else None
            }
        
        error_response = ErrorResponse(
            error_type=error_type,
            message=exc.message,
            details=error_details if error_details else None,
            request_id=request_id,
            debug_info=debug_info
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump(mode='json')
        )
    
    async def _handle_unexpected_error(
        self,
        exc: Exception,
        request_id: str
    ) -> JSONResponse:
        """Handle unexpected errors."""
        # Log full traceback for unexpected errors
        logger.error(
            f"Unexpected error in request {request_id}: {type(exc).__name__}: {str(exc)}",
            extra={
                "request_id": request_id,
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            }
        )
        
        debug_info = None
        if self.debug:
            debug_info = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc()
            }
        
        error_response = ErrorResponse(
            error_type=ErrorType.INTERNAL_ERROR,
            message="An unexpected error occurred",
            request_id=request_id,
            debug_info=debug_info
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(mode='json', by_alias=True, exclude_none=True)
        )
    
    def _get_status_code_from_error_code(self, error_code: ErrorCode) -> int:
        """Map error codes to HTTP status codes."""
        mapping = {
            ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
            ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.AUTHENTICATION_REQUIRED: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.ACCESS_DENIED: status.HTTP_403_FORBIDDEN,
            ErrorCode.TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
            ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCode.BUSINESS_RULE_VIOLATION: status.HTTP_400_BAD_REQUEST,
            ErrorCode.INVALID_OPERATION: status.HTTP_400_BAD_REQUEST,
            ErrorCode.EXTERNAL_SERVICE_ERROR: status.HTTP_502_BAD_GATEWAY,
            ErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCode.TIMEOUT_ERROR: status.HTTP_504_GATEWAY_TIMEOUT,
            ErrorCode.UNKNOWN_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        return mapping.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_error_type_from_error_code(self, error_code: ErrorCode) -> ErrorType:
        """Map error codes to error types."""
        mapping = {
            ErrorCode.VALIDATION_ERROR: ErrorType.VALIDATION_ERROR,
            ErrorCode.NOT_FOUND: ErrorType.NOT_FOUND_ERROR,
            ErrorCode.AUTHENTICATION_REQUIRED: ErrorType.AUTHENTICATION_ERROR,
            ErrorCode.INVALID_CREDENTIALS: ErrorType.AUTHENTICATION_ERROR,
            ErrorCode.ACCESS_DENIED: ErrorType.AUTHORIZATION_ERROR,
            ErrorCode.TOKEN_EXPIRED: ErrorType.AUTHENTICATION_ERROR,
            ErrorCode.CONFLICT: ErrorType.CONFLICT_ERROR,
            ErrorCode.RATE_LIMIT_EXCEEDED: ErrorType.RATE_LIMIT_ERROR,
            ErrorCode.EXTERNAL_SERVICE_ERROR: ErrorType.SERVICE_UNAVAILABLE,
            ErrorCode.SERVICE_UNAVAILABLE: ErrorType.SERVICE_UNAVAILABLE,
            ErrorCode.TIMEOUT_ERROR: ErrorType.SERVICE_UNAVAILABLE
        }
        return mapping.get(error_code, ErrorType.INTERNAL_ERROR)
    
    def _get_error_type_from_status(self, status_code: int) -> ErrorType:
        """Map HTTP status codes to error types."""
        if status_code == 400:
            return ErrorType.VALIDATION_ERROR
        elif status_code == 401:
            return ErrorType.AUTHENTICATION_ERROR
        elif status_code == 403:
            return ErrorType.AUTHORIZATION_ERROR
        elif status_code == 404:
            return ErrorType.NOT_FOUND_ERROR
        elif status_code == 409:
            return ErrorType.CONFLICT_ERROR
        elif status_code == 429:
            return ErrorType.RATE_LIMIT_ERROR
        elif status_code >= 500:
            return ErrorType.INTERNAL_ERROR
        else:
            return ErrorType.INTERNAL_ERROR


def setup_error_handlers(app):
    """Setup error handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Add error handling middleware
    from src.infrastructure.config import get_settings
    settings = get_settings()
    debug = settings.app_environment == "development"
    
    app.add_middleware(ErrorHandlingMiddleware, debug=debug)
    
    # Override FastAPI's default exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        error_type = ErrorType.INTERNAL_ERROR
        if exc.status_code == 400:
            error_type = ErrorType.VALIDATION_ERROR
        elif exc.status_code == 401:
            error_type = ErrorType.AUTHENTICATION_ERROR
        elif exc.status_code == 403:
            error_type = ErrorType.AUTHORIZATION_ERROR
        elif exc.status_code == 404:
            error_type = ErrorType.NOT_FOUND_ERROR
        elif exc.status_code == 409:
            error_type = ErrorType.CONFLICT_ERROR
        elif exc.status_code == 429:
            error_type = ErrorType.RATE_LIMIT_ERROR
        elif exc.status_code >= 500:
            error_type = ErrorType.INTERNAL_ERROR
        
        error_response = ErrorResponse(
            error_type=error_type,
            message=exc.detail if isinstance(exc.detail, str) else "HTTP error occurred",
            request_id=request_id,
            debug_info={"status_code": exc.status_code} if debug else None
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(mode='json')
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        
        error_details = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            # Ensure message is a string to avoid serialization issues
            message = str(error["msg"]) if error["msg"] is not None else "Validation error"
            error_detail = ErrorDetail(
                field=field_path,
                message=message,
                code=error["type"]
            )
            error_details.append(error_detail)
        
        # Prepare debug info with proper serialization
        debug_info = None
        if debug:
            debug_info = {"raw_errors": exc.errors()}
        
        error_response = ErrorResponse(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Request validation failed",
            details=error_details,
            request_id=request_id,
            debug_info=debug_info
        )
        
        # Manual serialization to avoid ValueError serialization issues
        try:
            content = error_response.model_dump(mode='json')
        except Exception as e:
            # Fallback to manual dict creation if model_dump fails
            content = {
                "status": "error",
                "error_type": "validation_error",
                "message": "Request validation failed",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "details": [
                    {
                        "field": detail.field,
                        "message": detail.message,
                        "code": detail.code
                    }
                    for detail in error_details
                ]
            }
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=content
        )
    
    # Custom exception handlers for specific cases
    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError):
        """Handle rate limit errors with retry-after header."""
        response_data = ErrorResponse(
            error_type=ErrorType.RATE_LIMIT_ERROR,
            message=exc.message,
            request_id=getattr(request.state, 'request_id', None)
        ).model_dump(mode='json')
        
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=response_data,
            headers=headers
        )
    
    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        """Handle service errors with fallback mechanisms."""
        # Log service errors for monitoring
        logger.warning(
            f"Service error: {exc.service_name} - {exc.operation}: {exc.message}",
            extra={
                "service_name": exc.service_name,
                "operation": exc.operation,
                "details": exc.details
            }
        )
        
        # Provide user-friendly message
        user_message = "A service is temporarily unavailable. Please try again later."
        if exc.service_name in ["openai", "openrouter", "llm"]:
            user_message = "AI service is temporarily unavailable. Please try again in a moment."
        elif exc.service_name == "database":
            user_message = "Data service is temporarily unavailable. Please try again later."
        
        response_data = ErrorResponse(
            error_type=ErrorType.SERVICE_UNAVAILABLE,
            message=user_message,
            request_id=getattr(request.state, 'request_id', None)
        ).model_dump(mode='json')
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data
        )
    
    logger.info("Error handlers configured successfully")