"""Base exception classes for the domain layer."""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes for the application."""
    
    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    
    # Authentication & Authorization
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCESS_DENIED = "ACCESS_DENIED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Business logic
    INVALID_OPERATION = "INVALID_OPERATION"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    
    # External services
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class DomainError(Exception):
    """Base exception for all domain-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize domain error.
        
        Args:
            message: Human-readable error message
            error_code: Standardized error code
            details: Additional error details
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "type": self.__class__.__name__
        }
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"{self.error_code.value}: {self.message}"


class ValidationError(DomainError):
    """Exception raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Field that failed validation
            value: Value that was rejected
            constraint: Validation constraint that failed
            details: Additional details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["rejected_value"] = value
        if constraint:
            error_details["constraint"] = constraint
            
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=error_details
        )
        self.field = field
        self.value = value
        self.constraint = constraint


class NotFoundError(DomainError):
    """Exception raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize not found error.
        
        Args:
            message: Error message
            resource_type: Type of resource that was not found
            resource_id: ID of resource that was not found
            details: Additional details
        """
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id:
            error_details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            details=error_details
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class AuthenticationError(DomainError):
    """Exception raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authentication error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_REQUIRED,
            details=details
        )


class AuthorizationError(DomainError):
    """Exception raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authorization error.
        
        Args:
            message: Error message
            required_permission: Permission that was required
            details: Additional details
        """
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
            
        super().__init__(
            message=message,
            error_code=ErrorCode.ACCESS_DENIED,
            details=error_details
        )
        self.required_permission = required_permission


class ConflictError(DomainError):
    """Exception raised when a resource conflict occurs."""
    
    def __init__(
        self,
        message: str,
        conflicting_resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize conflict error.
        
        Args:
            message: Error message
            conflicting_resource: Resource that caused the conflict
            details: Additional details
        """
        error_details = details or {}
        if conflicting_resource:
            error_details["conflicting_resource"] = conflicting_resource
            
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            details=error_details
        )
        self.conflicting_resource = conflicting_resource


class RateLimitError(DomainError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize rate limit error.
        
        Args:
            message: Error message
            limit: Rate limit threshold
            window_seconds: Time window for rate limit
            retry_after: Seconds to wait before retrying
            details: Additional details
        """
        error_details = details or {}
        if limit:
            error_details["limit"] = limit
        if window_seconds:
            error_details["window_seconds"] = window_seconds
        if retry_after:
            error_details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            details=error_details
        )
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after