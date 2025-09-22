"""Service-specific exception classes."""

from typing import Optional, Dict, Any
from .base_exceptions import DomainError, ErrorCode


class ServiceError(DomainError):
    """Base exception for service-related errors."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize service error.
        
        Args:
            message: Error message
            service_name: Name of the service that failed
            operation: Operation that was being performed
            details: Additional details
        """
        error_details = details or {}
        if service_name:
            error_details["service_name"] = service_name
        if operation:
            error_details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            details=error_details
        )
        self.service_name = service_name
        self.operation = operation


class OpenAIServiceError(ServiceError):
    """Exception raised when OpenAI service fails."""
    
    def __init__(
        self,
        message: str,
        api_error_code: Optional[str] = None,
        api_error_type: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize OpenAI service error.
        
        Args:
            message: Error message
            api_error_code: OpenAI API error code
            api_error_type: OpenAI API error type
            request_id: OpenAI request ID
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if api_error_code:
            details["api_error_code"] = api_error_code
        if api_error_type:
            details["api_error_type"] = api_error_type
        if request_id:
            details["request_id"] = request_id
            
        kwargs['details'] = details
        kwargs['service_name'] = "openai"
        super().__init__(message, **kwargs)
        self.api_error_code = api_error_code
        self.api_error_type = api_error_type
        self.request_id = request_id


class MemoryManagerError(ServiceError):
    """Exception raised when memory manager fails."""
    
    def __init__(
        self,
        message: str,
        cache_operation: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize memory manager error.
        
        Args:
            message: Error message
            cache_operation: Cache operation that failed
            session_id: Session ID related to the error
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if cache_operation:
            details["cache_operation"] = cache_operation
        if session_id:
            details["session_id"] = session_id
            
        kwargs['details'] = details
        kwargs['service_name'] = "memory_manager"
        super().__init__(message, **kwargs)
        self.cache_operation = cache_operation
        self.session_id = session_id


class PedagogyEngineError(ServiceError):
    """Exception raised when pedagogy engine fails."""
    
    def __init__(
        self,
        message: str,
        processing_stage: Optional[str] = None,
        input_data: Optional[str] = None,
        **kwargs
    ):
        """Initialize pedagogy engine error.
        
        Args:
            message: Error message
            processing_stage: Stage where processing failed
            input_data: Input data that caused the error
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if processing_stage:
            details["processing_stage"] = processing_stage
        if input_data:
            details["input_data"] = input_data[:200]  # Truncate for safety
            
        kwargs['details'] = details
        kwargs['service_name'] = "pedagogy_engine"
        super().__init__(message, **kwargs)
        self.processing_stage = processing_stage
        self.input_data = input_data


class DatabaseError(ServiceError):
    """Exception raised when database operations fail."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        constraint: Optional[str] = None,
        **kwargs
    ):
        """Initialize database error.
        
        Args:
            message: Error message
            operation: Database operation that failed
            table: Database table involved
            constraint: Database constraint that was violated
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        if constraint:
            details["constraint"] = constraint
            
        kwargs['details'] = details
        kwargs['service_name'] = "database"
        super().__init__(message, **kwargs)
        self.operation = operation
        self.table = table
        self.constraint = constraint


class ExternalServiceError(ServiceError):
    """Exception raised when external service calls fail."""
    
    def __init__(
        self,
        message: str,
        service_url: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ):
        """Initialize external service error.
        
        Args:
            message: Error message
            service_url: URL of the external service
            status_code: HTTP status code returned
            response_body: Response body from the service
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if service_url:
            details["service_url"] = service_url
        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:500]  # Truncate for safety
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.service_url = service_url
        self.status_code = status_code
        self.response_body = response_body


class TimeoutError(ServiceError):
    """Exception raised when service operations timeout."""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        **kwargs
    ):
        """Initialize timeout error.
        
        Args:
            message: Error message
            timeout_seconds: Timeout duration in seconds
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.error_code = ErrorCode.TIMEOUT_ERROR
        self.timeout_seconds = timeout_seconds


class ServiceUnavailableError(ServiceError):
    """Exception raised when service is unavailable."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        """Initialize service unavailable error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if retry_after:
            details["retry_after"] = retry_after
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.error_code = ErrorCode.SERVICE_UNAVAILABLE
        self.retry_after = retry_after


class ConfigurationError(ServiceError):
    """Exception raised when service configuration is invalid."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[str] = None,
        **kwargs
    ):
        """Initialize configuration error.
        
        Args:
            message: Error message
            config_key: Configuration key that is invalid
            config_value: Configuration value that is invalid
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        if config_key:
            details["config_key"] = config_key
        if config_value:
            details["config_value"] = config_value
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value


class RetryExhaustedError(ServiceError):
    """Exception raised when retry attempts are exhausted."""
    
    def __init__(
        self,
        message: str,
        max_retries: int,
        last_error: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize retry exhausted error.
        
        Args:
            message: Error message
            max_retries: Maximum number of retries attempted
            last_error: Last error that occurred
            **kwargs: Additional arguments for ServiceError
        """
        details = kwargs.get('details', {})
        details["max_retries"] = max_retries
        if last_error:
            details["last_error"] = str(last_error)
            
        kwargs['details'] = details
        super().__init__(message, cause=last_error, **kwargs)
        self.max_retries = max_retries
        self.last_error = last_error