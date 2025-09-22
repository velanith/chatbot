"""Assessment-specific exception classes."""

from typing import Optional, Dict, Any, List
from .base_exceptions import DomainError, ErrorCode


class AssessmentError(DomainError):
    """Base exception for assessment-related errors."""
    
    def __init__(
        self,
        message: str,
        assessment_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize assessment error.
        
        Args:
            message: Error message
            assessment_id: Assessment ID where error occurred
            user_id: User ID associated with error
            details: Additional details
        """
        error_details = details or {}
        if assessment_id:
            error_details["assessment_id"] = assessment_id
        if user_id:
            error_details["user_id"] = user_id
            
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            details=error_details
        )
        self.assessment_id = assessment_id
        self.user_id = user_id


class AssessmentNotFoundError(AssessmentError):
    """Exception raised when assessment session is not found."""
    
    def __init__(
        self,
        assessment_id: str,
        message: str = "Assessment session not found",
        **kwargs
    ):
        """Initialize assessment not found error."""
        super().__init__(
            message=message,
            assessment_id=assessment_id,
            **kwargs
        )
        self.error_code = ErrorCode.NOT_FOUND


class AssessmentCreationError(AssessmentError):
    """Exception raised when assessment creation fails."""
    
    def __init__(
        self,
        message: str,
        language_pair: Optional[str] = None,
        creation_reason: Optional[str] = None,
        **kwargs
    ):
        """Initialize assessment creation error.
        
        Args:
            message: Error message
            language_pair: Language pair for the assessment
            creation_reason: Reason why assessment creation failed
            **kwargs: Additional arguments for AssessmentError
        """
        details = kwargs.get('details', {})
        if language_pair:
            details["language_pair"] = language_pair
        if creation_reason:
            details["creation_reason"] = creation_reason
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.language_pair = language_pair
        self.creation_reason = creation_reason


class AssessmentStateError(AssessmentError):
    """Exception raised when assessment is in invalid state for operation."""
    
    def __init__(
        self,
        message: str,
        current_state: str,
        required_state: str,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize assessment state error.
        
        Args:
            message: Error message
            current_state: Current assessment state
            required_state: Required state for operation
            operation: Operation that was attempted
            **kwargs: Additional arguments for AssessmentError
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


class AssessmentResponseError(AssessmentError):
    """Exception raised when assessment response processing fails."""
    
    def __init__(
        self,
        message: str,
        response_content: Optional[str] = None,
        question_id: Optional[str] = None,
        processing_stage: Optional[str] = None,
        **kwargs
    ):
        """Initialize assessment response error.
        
        Args:
            message: Error message
            response_content: Response content that caused error
            question_id: Question ID being processed
            processing_stage: Stage where processing failed
            **kwargs: Additional arguments for AssessmentError
        """
        details = kwargs.get('details', {})
        if response_content:
            details["response_content"] = response_content[:200]  # Truncate for safety
        if question_id:
            details["question_id"] = question_id
        if processing_stage:
            details["processing_stage"] = processing_stage
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.response_content = response_content
        self.question_id = question_id
        self.processing_stage = processing_stage


class AssessmentEvaluationError(AssessmentError):
    """Exception raised when assessment evaluation fails."""
    
    def __init__(
        self,
        message: str,
        evaluation_type: Optional[str] = None,
        ai_response: Optional[str] = None,
        **kwargs
    ):
        """Initialize assessment evaluation error.
        
        Args:
            message: Error message
            evaluation_type: Type of evaluation that failed
            ai_response: AI response that caused error
            **kwargs: Additional arguments for AssessmentError
        """
        details = kwargs.get('details', {})
        if evaluation_type:
            details["evaluation_type"] = evaluation_type
        if ai_response:
            details["ai_response"] = ai_response[:300]  # Truncate for safety
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.evaluation_type = evaluation_type
        self.ai_response = ai_response


class AssessmentCompletionError(AssessmentError):
    """Exception raised when assessment completion fails."""
    
    def __init__(
        self,
        message: str,
        completion_stage: Optional[str] = None,
        responses_count: Optional[int] = None,
        min_required: Optional[int] = None,
        **kwargs
    ):
        """Initialize assessment completion error.
        
        Args:
            message: Error message
            completion_stage: Stage where completion failed
            responses_count: Number of responses received
            min_required: Minimum responses required
            **kwargs: Additional arguments for AssessmentError
        """
        details = kwargs.get('details', {})
        if completion_stage:
            details["completion_stage"] = completion_stage
        if responses_count is not None:
            details["responses_count"] = responses_count
        if min_required is not None:
            details["min_required"] = min_required
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.completion_stage = completion_stage
        self.responses_count = responses_count
        self.min_required = min_required


class AssessmentValidationError(AssessmentError):
    """Exception raised when assessment data validation fails."""
    
    def __init__(
        self,
        message: str,
        validation_field: Optional[str] = None,
        validation_rule: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize assessment validation error.
        
        Args:
            message: Error message
            validation_field: Field that failed validation
            validation_rule: Validation rule that failed
            provided_value: Value that was provided
            **kwargs: Additional arguments for AssessmentError
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


class AssessmentTimeoutError(AssessmentError):
    """Exception raised when assessment times out."""
    
    def __init__(
        self,
        message: str,
        timeout_duration: Optional[int] = None,
        elapsed_time: Optional[int] = None,
        **kwargs
    ):
        """Initialize assessment timeout error.
        
        Args:
            message: Error message
            timeout_duration: Timeout duration in seconds
            elapsed_time: Time elapsed before timeout
            **kwargs: Additional arguments for AssessmentError
        """
        details = kwargs.get('details', {})
        if timeout_duration:
            details["timeout_duration"] = timeout_duration
        if elapsed_time:
            details["elapsed_time"] = elapsed_time
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.error_code = ErrorCode.TIMEOUT_ERROR
        self.timeout_duration = timeout_duration
        self.elapsed_time = elapsed_time


class AssessmentLimitError(AssessmentError):
    """Exception raised when assessment limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: int,
        limit_value: int,
        **kwargs
    ):
        """Initialize assessment limit error.
        
        Args:
            message: Error message
            limit_type: Type of limit exceeded
            current_value: Current value that exceeded limit
            limit_value: The limit that was exceeded
            **kwargs: Additional arguments for AssessmentError
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


class InvalidLanguagePairError(AssessmentValidationError):
    """Exception raised when language pair is invalid."""
    
    def __init__(
        self,
        native_language: str,
        target_language: str,
        supported_pairs: Optional[List[str]] = None,
        message: str = "Invalid language pair",
        **kwargs
    ):
        """Initialize invalid language pair error.
        
        Args:
            native_language: Native language code
            target_language: Target language code
            supported_pairs: List of supported language pairs
            message: Error message
            **kwargs: Additional arguments for AssessmentValidationError
        """
        details = kwargs.get('details', {})
        details.update({
            "native_language": native_language,
            "target_language": target_language
        })
        if supported_pairs:
            details["supported_pairs"] = supported_pairs
            
        kwargs['details'] = details
        super().__init__(
            message=message,
            validation_field="language_pair",
            validation_rule="supported_language_pair",
            provided_value=f"{native_language}-{target_language}",
            **kwargs
        )
        self.native_language = native_language
        self.target_language = target_language
        self.supported_pairs = supported_pairs


class AssessmentAlreadyCompletedError(AssessmentStateError):
    """Exception raised when trying to modify completed assessment."""
    
    def __init__(
        self,
        assessment_id: str,
        completion_date: Optional[str] = None,
        message: str = "Assessment already completed",
        **kwargs
    ):
        """Initialize assessment already completed error."""
        details = kwargs.get('details', {})
        if completion_date:
            details["completion_date"] = completion_date
            
        kwargs['details'] = details
        super().__init__(
            message=message,
            current_state="completed",
            required_state="active",
            assessment_id=assessment_id,
            **kwargs
        )
        self.completion_date = completion_date


class AssessmentQuestionGenerationError(AssessmentError):
    """Exception raised when assessment question generation fails."""
    
    def __init__(
        self,
        message: str,
        question_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        generation_attempt: Optional[int] = None,
        **kwargs
    ):
        """Initialize assessment question generation error.
        
        Args:
            message: Error message
            question_type: Type of question being generated
            difficulty_level: Difficulty level of question
            generation_attempt: Which generation attempt failed
            **kwargs: Additional arguments for AssessmentError
        """
        details = kwargs.get('details', {})
        if question_type:
            details["question_type"] = question_type
        if difficulty_level:
            details["difficulty_level"] = difficulty_level
        if generation_attempt:
            details["generation_attempt"] = generation_attempt
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.question_type = question_type
        self.difficulty_level = difficulty_level
        self.generation_attempt = generation_attempt