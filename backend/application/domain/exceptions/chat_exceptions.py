"""Chat-specific exception classes."""

from typing import Optional, Dict, Any
from .base_exceptions import DomainError, ErrorCode


class ChatError(DomainError):
    """Base exception for chat-related errors."""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize chat error.
        
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


class InvalidMessageError(ChatError):
    """Exception raised when a message is invalid."""
    
    def __init__(
        self,
        message: str,
        message_content: Optional[str] = None,
        validation_reason: Optional[str] = None,
        **kwargs
    ):
        """Initialize invalid message error.
        
        Args:
            message: Error message
            message_content: The invalid message content
            validation_reason: Reason why message is invalid
            **kwargs: Additional arguments for ChatError
        """
        details = kwargs.get('details', {})
        if message_content:
            details["message_content"] = message_content[:100]  # Truncate for safety
        if validation_reason:
            details["validation_reason"] = validation_reason
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.message_content = message_content
        self.validation_reason = validation_reason


class SessionNotFoundError(ChatError):
    """Exception raised when a chat session is not found."""
    
    def __init__(
        self,
        session_id: str,
        message: str = "Chat session not found",
        **kwargs
    ):
        """Initialize session not found error."""
        super().__init__(
            message=message,
            session_id=session_id,
            **kwargs
        )
        self.error_code = ErrorCode.NOT_FOUND


class MessageProcessingError(ChatError):
    """Exception raised when message processing fails."""
    
    def __init__(
        self,
        message: str,
        processing_stage: Optional[str] = None,
        original_error: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize message processing error.
        
        Args:
            message: Error message
            processing_stage: Stage where processing failed
            original_error: Original exception that caused the error
            **kwargs: Additional arguments for ChatError
        """
        details = kwargs.get('details', {})
        if processing_stage:
            details["processing_stage"] = processing_stage
        if original_error:
            details["original_error"] = str(original_error)
            
        kwargs['details'] = details
        super().__init__(message, cause=original_error, **kwargs)
        self.processing_stage = processing_stage


class CorrectionError(ChatError):
    """Exception raised when correction processing fails."""
    
    def __init__(
        self,
        message: str,
        correction_type: Optional[str] = None,
        original_text: Optional[str] = None,
        **kwargs
    ):
        """Initialize correction error.
        
        Args:
            message: Error message
            correction_type: Type of correction that failed
            original_text: Original text being corrected
            **kwargs: Additional arguments for ChatError
        """
        details = kwargs.get('details', {})
        if correction_type:
            details["correction_type"] = correction_type
        if original_text:
            details["original_text"] = original_text[:100]  # Truncate for safety
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.correction_type = correction_type
        self.original_text = original_text


class ExerciseGenerationError(ChatError):
    """Exception raised when exercise generation fails."""
    
    def __init__(
        self,
        message: str,
        exercise_type: Optional[str] = None,
        context: Optional[str] = None,
        **kwargs
    ):
        """Initialize exercise generation error.
        
        Args:
            message: Error message
            exercise_type: Type of exercise that failed to generate
            context: Context used for exercise generation
            **kwargs: Additional arguments for ChatError
        """
        details = kwargs.get('details', {})
        if exercise_type:
            details["exercise_type"] = exercise_type
        if context:
            details["context"] = context[:200]  # Truncate for safety
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.exercise_type = exercise_type
        self.context = context


class ConversationLimitError(ChatError):
    """Exception raised when conversation limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: int,
        limit_value: int,
        **kwargs
    ):
        """Initialize conversation limit error.
        
        Args:
            message: Error message
            limit_type: Type of limit exceeded (messages, tokens, etc.)
            current_value: Current value that exceeded limit
            limit_value: The limit that was exceeded
            **kwargs: Additional arguments for ChatError
        """
        details = kwargs.get('details', {})
        details.update({
            "limit_type": limit_type,
            "current_value": current_value,
            "limit_value": limit_value
        })
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.limit_type = limit_type
        self.current_value = current_value
        self.limit_value = limit_value


class MessageTooLongError(InvalidMessageError):
    """Exception raised when a message is too long."""
    
    def __init__(
        self,
        message_length: int,
        max_length: int,
        message: str = "Message exceeds maximum length",
        **kwargs
    ):
        """Initialize message too long error."""
        details = kwargs.get('details', {})
        details.update({
            "message_length": message_length,
            "max_length": max_length
        })
        
        kwargs['details'] = details
        super().__init__(
            message=message,
            validation_reason=f"Message length {message_length} exceeds maximum {max_length}",
            **kwargs
        )
        self.message_length = message_length
        self.max_length = max_length


class MessageTooShortError(InvalidMessageError):
    """Exception raised when a message is too short."""
    
    def __init__(
        self,
        message_length: int,
        min_length: int,
        message: str = "Message is too short",
        **kwargs
    ):
        """Initialize message too short error."""
        details = kwargs.get('details', {})
        details.update({
            "message_length": message_length,
            "min_length": min_length
        })
        
        kwargs['details'] = details
        super().__init__(
            message=message,
            validation_reason=f"Message length {message_length} is below minimum {min_length}",
            **kwargs
        )
        self.message_length = message_length
        self.min_length = min_length


class ForbiddenContentError(InvalidMessageError):
    """Exception raised when message contains forbidden content."""
    
    def __init__(
        self,
        content_type: str,
        detected_content: Optional[str] = None,
        message: str = "Message contains forbidden content",
        **kwargs
    ):
        """Initialize forbidden content error.
        
        Args:
            content_type: Type of forbidden content detected
            detected_content: The specific content that was detected
            message: Error message
            **kwargs: Additional arguments for InvalidMessageError
        """
        details = kwargs.get('details', {})
        details.update({
            "content_type": content_type,
            "detected_content": detected_content
        })
        
        kwargs['details'] = details
        super().__init__(
            message=message,
            validation_reason=f"Forbidden content detected: {content_type}",
            **kwargs
        )
        self.content_type = content_type
        self.detected_content = detected_content