"""Topic-specific exception classes."""

from typing import Optional, Dict, Any, List
from .base_exceptions import DomainError, ErrorCode


class TopicError(DomainError):
    """Base exception for topic-related errors."""
    
    def __init__(
        self,
        message: str,
        topic_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize topic error.
        
        Args:
            message: Error message
            topic_id: Topic ID where error occurred
            session_id: Session ID associated with error
            user_id: User ID associated with error
            details: Additional details
        """
        error_details = details or {}
        if topic_id:
            error_details["topic_id"] = topic_id
        if session_id:
            error_details["session_id"] = session_id
        if user_id:
            error_details["user_id"] = user_id
            
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            details=error_details
        )
        self.topic_id = topic_id
        self.session_id = session_id
        self.user_id = user_id


class TopicNotFoundError(TopicError):
    """Exception raised when topic is not found."""
    
    def __init__(
        self,
        topic_id: str,
        message: str = "Topic not found",
        **kwargs
    ):
        """Initialize topic not found error."""
        super().__init__(
            message=message,
            topic_id=topic_id,
            **kwargs
        )
        self.error_code = ErrorCode.NOT_FOUND


class TopicSelectionError(TopicError):
    """Exception raised when topic selection fails."""
    
    def __init__(
        self,
        message: str,
        selection_criteria: Optional[Dict[str, Any]] = None,
        available_topics: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize topic selection error.
        
        Args:
            message: Error message
            selection_criteria: Criteria used for topic selection
            available_topics: List of available topic IDs
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        if selection_criteria:
            details["selection_criteria"] = selection_criteria
        if available_topics:
            details["available_topics"] = available_topics[:10]  # Limit for safety
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.selection_criteria = selection_criteria
        self.available_topics = available_topics


class TopicSuggestionError(TopicError):
    """Exception raised when topic suggestion fails."""
    
    def __init__(
        self,
        message: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        proficiency_level: Optional[str] = None,
        suggestion_algorithm: Optional[str] = None,
        **kwargs
    ):
        """Initialize topic suggestion error.
        
        Args:
            message: Error message
            user_preferences: User preferences used for suggestion
            proficiency_level: User's proficiency level
            suggestion_algorithm: Algorithm used for suggestion
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        if user_preferences:
            details["user_preferences"] = user_preferences
        if proficiency_level:
            details["proficiency_level"] = proficiency_level
        if suggestion_algorithm:
            details["suggestion_algorithm"] = suggestion_algorithm
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.user_preferences = user_preferences
        self.proficiency_level = proficiency_level
        self.suggestion_algorithm = suggestion_algorithm


class TopicValidationError(TopicError):
    """Exception raised when topic data validation fails."""
    
    def __init__(
        self,
        message: str,
        validation_field: Optional[str] = None,
        validation_rule: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize topic validation error.
        
        Args:
            message: Error message
            validation_field: Field that failed validation
            validation_rule: Validation rule that failed
            provided_value: Value that was provided
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        if validation_field:
            details["validation_field"] = validation_field
        if validation_rule:
            details["validation_rule"] = validation_rule
        if provided_value is not None:
            details["provided_value"] = str(provided_value)
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.error_code = ErrorCode.VALIDATION_ERROR
        self.validation_field = validation_field
        self.validation_rule = validation_rule
        self.provided_value = provided_value


class TopicCoherenceError(TopicError):
    """Exception raised when topic coherence check fails."""
    
    def __init__(
        self,
        message: str,
        current_topic: Optional[str] = None,
        conversation_messages: Optional[int] = None,
        coherence_score: Optional[float] = None,
        **kwargs
    ):
        """Initialize topic coherence error.
        
        Args:
            message: Error message
            current_topic: Current topic being checked
            conversation_messages: Number of messages in conversation
            coherence_score: Calculated coherence score
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        if current_topic:
            details["current_topic"] = current_topic
        if conversation_messages:
            details["conversation_messages"] = conversation_messages
        if coherence_score is not None:
            details["coherence_score"] = coherence_score
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.current_topic = current_topic
        self.conversation_messages = conversation_messages
        self.coherence_score = coherence_score


class TopicTransitionError(TopicError):
    """Exception raised when topic transition fails."""
    
    def __init__(
        self,
        message: str,
        from_topic: Optional[str] = None,
        to_topic: Optional[str] = None,
        transition_reason: Optional[str] = None,
        **kwargs
    ):
        """Initialize topic transition error.
        
        Args:
            message: Error message
            from_topic: Topic being transitioned from
            to_topic: Topic being transitioned to
            transition_reason: Reason for transition
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        if from_topic:
            details["from_topic"] = from_topic
        if to_topic:
            details["to_topic"] = to_topic
        if transition_reason:
            details["transition_reason"] = transition_reason
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.from_topic = from_topic
        self.to_topic = to_topic
        self.transition_reason = transition_reason


class TopicStarterGenerationError(TopicError):
    """Exception raised when topic starter generation fails."""
    
    def __init__(
        self,
        message: str,
        topic_category: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        generation_attempt: Optional[int] = None,
        **kwargs
    ):
        """Initialize topic starter generation error.
        
        Args:
            message: Error message
            topic_category: Category of topic for starter
            difficulty_level: Difficulty level for starter
            generation_attempt: Which generation attempt failed
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        if topic_category:
            details["topic_category"] = topic_category
        if difficulty_level:
            details["difficulty_level"] = difficulty_level
        if generation_attempt:
            details["generation_attempt"] = generation_attempt
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.topic_category = topic_category
        self.difficulty_level = difficulty_level
        self.generation_attempt = generation_attempt


class InvalidTopicCategoryError(TopicValidationError):
    """Exception raised when topic category is invalid."""
    
    def __init__(
        self,
        category: str,
        supported_categories: Optional[List[str]] = None,
        message: str = "Invalid topic category",
        **kwargs
    ):
        """Initialize invalid topic category error.
        
        Args:
            category: Invalid category provided
            supported_categories: List of supported categories
            message: Error message
            **kwargs: Additional arguments for TopicValidationError
        """
        details = kwargs.get('details', {})
        if supported_categories:
            details["supported_categories"] = supported_categories
            
        kwargs['details'] = details
        super().__init__(
            message=message,
            validation_field="category",
            validation_rule="supported_category",
            provided_value=category,
            **kwargs
        )
        self.category = category
        self.supported_categories = supported_categories


class TopicDifficultyMismatchError(TopicError):
    """Exception raised when topic difficulty doesn't match user level."""
    
    def __init__(
        self,
        message: str,
        topic_difficulty: str,
        user_level: str,
        difficulty_gap: Optional[int] = None,
        **kwargs
    ):
        """Initialize topic difficulty mismatch error.
        
        Args:
            message: Error message
            topic_difficulty: Difficulty level of topic
            user_level: User's proficiency level
            difficulty_gap: Gap between levels (positive = too hard, negative = too easy)
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        details.update({
            "topic_difficulty": topic_difficulty,
            "user_level": user_level
        })
        if difficulty_gap is not None:
            details["difficulty_gap"] = difficulty_gap
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.topic_difficulty = topic_difficulty
        self.user_level = user_level
        self.difficulty_gap = difficulty_gap


class TopicDataCorruptionError(TopicError):
    """Exception raised when topic data is corrupted or incomplete."""
    
    def __init__(
        self,
        message: str,
        missing_fields: Optional[List[str]] = None,
        corrupted_fields: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize topic data corruption error.
        
        Args:
            message: Error message
            missing_fields: List of missing required fields
            corrupted_fields: List of fields with corrupted data
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        if missing_fields:
            details["missing_fields"] = missing_fields
        if corrupted_fields:
            details["corrupted_fields"] = corrupted_fields
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.missing_fields = missing_fields
        self.corrupted_fields = corrupted_fields


class TopicLimitError(TopicError):
    """Exception raised when topic limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: int,
        limit_value: int,
        **kwargs
    ):
        """Initialize topic limit error.
        
        Args:
            message: Error message
            limit_type: Type of limit exceeded
            current_value: Current value that exceeded limit
            limit_value: The limit that was exceeded
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        details.update({
            "limit_type": limit_type,
            "current_value": current_value,
            "limit_value": limit_value
        })
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.error_code = ErrorCode.RATE_LIMIT_EXCEEDED
        self.limit_type = limit_type
        self.current_value = current_value
        self.limit_value = limit_value


class TopicCacheError(TopicError):
    """Exception raised when topic caching operations fail."""
    
    def __init__(
        self,
        message: str,
        cache_operation: str,
        cache_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize topic cache error.
        
        Args:
            message: Error message
            cache_operation: Cache operation that failed
            cache_key: Cache key involved in operation
            **kwargs: Additional arguments for TopicError
        """
        details = kwargs.get('details', {})
        details["cache_operation"] = cache_operation
        if cache_key:
            details["cache_key"] = cache_key
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.cache_operation = cache_operation
        self.cache_key = cache_key