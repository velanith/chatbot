"""Session-specific exception classes."""

from typing import Optional, Dict, Any
from .base_exceptions import DomainError, ErrorCode


class SessionError(DomainError):
    """Base exception for session-related errors."""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize session error.
        
        Args:
            message: Error message
            session_id: Session ID where error occurred
            user_id: User ID associated with error
            details: Additional details
        """
        error_details = details or {}
        if session_id:
            error_details["session_id"] = session_id
        if user_id:
            error_details["user_id"] = user_id
            
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            details=error_details
        )
        self.session_id = session_id
        self.user_id = user_id


class SessionCreationError(SessionError):
    """Exception raised when session creation fails."""
    
    def __init__(
        self,
        message: str,
        creation_reason: Optional[str] = None,
        **kwargs
    ):
        """Initialize session creation error.
        
        Args:
            message: Error message
            creation_reason: Reason why session creation failed
            **kwargs: Additional arguments for SessionError
        """
        details = kwargs.get('details', {})
        if creation_reason:
            details["creation_reason"] = creation_reason
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.creation_reason = creation_reason


class SessionUpdateError(SessionError):
    """Exception raised when session update fails."""
    
    def __init__(
        self,
        message: str,
        update_field: Optional[str] = None,
        update_value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize session update error.
        
        Args:
            message: Error message
            update_field: Field that failed to update
            update_value: Value that failed to be set
            **kwargs: Additional arguments for SessionError
        """
        details = kwargs.get('details', {})
        if update_field:
            details["update_field"] = update_field
        if update_value is not None:
            details["update_value"] = str(update_value)
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.update_field = update_field
        self.update_value = update_value


class SessionAccessError(SessionError):
    """Exception raised when session access is denied."""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        message: str = "Access denied to session",
        access_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize session access error.
        
        Args:
            session_id: Session ID that was accessed
            user_id: User ID that attempted access
            message: Error message
            access_type: Type of access that was denied
            **kwargs: Additional arguments for SessionError
        """
        details = kwargs.get('details', {})
        if access_type:
            details["access_type"] = access_type
            
        kwargs['details'] = details
        super().__init__(
            message=message,
            session_id=session_id,
            user_id=user_id,
            **kwargs
        )
        self.error_code = ErrorCode.ACCESS_DENIED
        self.access_type = access_type


class SessionExpiredError(SessionError):
    """Exception raised when session has expired."""
    
    def __init__(
        self,
        session_id: str,
        expiry_time: Optional[str] = None,
        message: str = "Session has expired",
        **kwargs
    ):
        """Initialize session expired error.
        
        Args:
            session_id: Expired session ID
            expiry_time: When the session expired
            message: Error message
            **kwargs: Additional arguments for SessionError
        """
        details = kwargs.get('details', {})
        if expiry_time:
            details["expiry_time"] = expiry_time
            
        kwargs['details'] = details
        super().__init__(
            message=message,
            session_id=session_id,
            **kwargs
        )
        self.expiry_time = expiry_time


class SessionCleanupError(SessionError):
    """Exception raised when session cleanup fails."""
    
    def __init__(
        self,
        message: str,
        cleanup_stage: Optional[str] = None,
        affected_sessions: Optional[int] = None,
        **kwargs
    ):
        """Initialize session cleanup error.
        
        Args:
            message: Error message
            cleanup_stage: Stage where cleanup failed
            affected_sessions: Number of sessions affected
            **kwargs: Additional arguments for SessionError
        """
        details = kwargs.get('details', {})
        if cleanup_stage:
            details["cleanup_stage"] = cleanup_stage
        if affected_sessions is not None:
            details["affected_sessions"] = affected_sessions
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.cleanup_stage = cleanup_stage
        self.affected_sessions = affected_sessions


class SessionLimitError(SessionError):
    """Exception raised when session limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_count: int,
        max_allowed: int,
        **kwargs
    ):
        """Initialize session limit error.
        
        Args:
            message: Error message
            limit_type: Type of limit exceeded
            current_count: Current count
            max_allowed: Maximum allowed count
            **kwargs: Additional arguments for SessionError
        """
        details = kwargs.get('details', {})
        details.update({
            "limit_type": limit_type,
            "current_count": current_count,
            "max_allowed": max_allowed
        })
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.limit_type = limit_type
        self.current_count = current_count
        self.max_allowed = max_allowed


class SessionStateError(SessionError):
    """Exception raised when session is in invalid state for operation."""
    
    def __init__(
        self,
        message: str,
        current_state: str,
        required_state: str,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize session state error.
        
        Args:
            message: Error message
            current_state: Current session state
            required_state: Required state for operation
            operation: Operation that was attempted
            **kwargs: Additional arguments for SessionError
        """
        details = kwargs.get('details', {})
        details.update({
            "current_state": current_state,
            "required_state": required_state
        })
        if operation:
            details["operation"] = operation
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.current_state = current_state
        self.required_state = required_state
        self.operation = operation


class SessionNotFoundError(SessionError):
    """Exception raised when session is not found."""
    
    def __init__(
        self,
        session_id: str,
        message: str = "Session not found",
        **kwargs
    ):
        """Initialize session not found error."""
        super().__init__(
            message=message,
            session_id=session_id,
            **kwargs
        )
        self.error_code = ErrorCode.NOT_FOUND


class SessionAlreadyExistsError(SessionError):
    """Exception raised when trying to create a session that already exists."""
    
    def __init__(
        self,
        session_id: str,
        message: str = "Session already exists",
        **kwargs
    ):
        """Initialize session already exists error."""
        super().__init__(
            message=message,
            session_id=session_id,
            **kwargs
        )
        self.error_code = ErrorCode.CONFLICT