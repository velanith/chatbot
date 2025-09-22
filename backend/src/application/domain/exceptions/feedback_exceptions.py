"""Feedback-specific exception classes."""

from typing import Optional, Dict, Any, List
from .base_exceptions import DomainError, ErrorCode


class FeedbackError(DomainError):
    """Base exception for feedback-related errors."""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        message_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize feedback error.
        
        Args:
            message: Error message
            session_id: Session ID where error occurred
            user_id: User ID associated with error
            message_count: Number of messages processed
            details: Additional details
        """
        error_details = details or {}
        if session_id:
            error_details["session_id"] = session_id
        if user_id:
            error_details["user_id"] = user_id
        if message_count is not None:
            error_details["message_count"] = message_count
            
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            details=error_details
        )
        self.session_id = session_id
        self.user_id = user_id
        self.message_count = message_count


class FeedbackGenerationError(FeedbackError):
    """Exception raised when feedback generation fails."""
    
    def __init__(
        self,
        message: str,
        feedback_type: Optional[str] = None,
        generation_stage: Optional[str] = None,
        input_messages: Optional[int] = None,
        **kwargs
    ):
        """Initialize feedback generation error.
        
        Args:
            message: Error message
            feedback_type: Type of feedback being generated
            generation_stage: Stage where generation failed
            input_messages: Number of input messages
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        if feedback_type:
            details["feedback_type"] = feedback_type
        if generation_stage:
            details["generation_stage"] = generation_stage
        if input_messages is not None:
            details["input_messages"] = input_messages
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.feedback_type = feedback_type
        self.generation_stage = generation_stage
        self.input_messages = input_messages


class StructuredFeedbackError(FeedbackError):
    """Exception raised when structured feedback processing fails."""
    
    def __init__(
        self,
        message: str,
        feedback_component: Optional[str] = None,
        processing_step: Optional[str] = None,
        **kwargs
    ):
        """Initialize structured feedback error.
        
        Args:
            message: Error message
            feedback_component: Component of feedback that failed
            processing_step: Processing step that failed
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        if feedback_component:
            details["feedback_component"] = feedback_component
        if processing_step:
            details["processing_step"] = processing_step
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.feedback_component = feedback_component
        self.processing_step = processing_step


class CorrectionGenerationError(FeedbackError):
    """Exception raised when correction generation fails."""
    
    def __init__(
        self,
        message: str,
        correction_type: Optional[str] = None,
        original_text: Optional[str] = None,
        error_category: Optional[str] = None,
        **kwargs
    ):
        """Initialize correction generation error.
        
        Args:
            message: Error message
            correction_type: Type of correction being generated
            original_text: Original text being corrected
            error_category: Category of error being corrected
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        if correction_type:
            details["correction_type"] = correction_type
        if original_text:
            details["original_text"] = original_text[:200]  # Truncate for safety
        if error_category:
            details["error_category"] = error_category
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.correction_type = correction_type
        self.original_text = original_text
        self.error_category = error_category


class GrammarFeedbackError(FeedbackError):
    """Exception raised when grammar feedback generation fails."""
    
    def __init__(
        self,
        message: str,
        grammar_rule: Optional[str] = None,
        text_segment: Optional[str] = None,
        analysis_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize grammar feedback error.
        
        Args:
            message: Error message
            grammar_rule: Grammar rule being analyzed
            text_segment: Text segment being analyzed
            analysis_type: Type of grammar analysis
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        if grammar_rule:
            details["grammar_rule"] = grammar_rule
        if text_segment:
            details["text_segment"] = text_segment[:150]  # Truncate for safety
        if analysis_type:
            details["analysis_type"] = analysis_type
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.grammar_rule = grammar_rule
        self.text_segment = text_segment
        self.analysis_type = analysis_type


class AlternativeExpressionError(FeedbackError):
    """Exception raised when alternative expression generation fails."""
    
    def __init__(
        self,
        message: str,
        original_expression: Optional[str] = None,
        context: Optional[str] = None,
        expression_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize alternative expression error.
        
        Args:
            message: Error message
            original_expression: Original expression being replaced
            context: Context for the expression
            expression_type: Type of expression (formal, informal, etc.)
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        if original_expression:
            details["original_expression"] = original_expression[:100]
        if context:
            details["context"] = context[:200]
        if expression_type:
            details["expression_type"] = expression_type
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.original_expression = original_expression
        self.context = context
        self.expression_type = expression_type


class FeedbackValidationError(FeedbackError):
    """Exception raised when feedback data validation fails."""
    
    def __init__(
        self,
        message: str,
        validation_field: Optional[str] = None,
        validation_rule: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize feedback validation error.
        
        Args:
            message: Error message
            validation_field: Field that failed validation
            validation_rule: Validation rule that failed
            provided_value: Value that was provided
            **kwargs: Additional arguments for FeedbackError
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


class FeedbackCycleError(FeedbackError):
    """Exception raised when feedback cycle management fails."""
    
    def __init__(
        self,
        message: str,
        cycle_stage: Optional[str] = None,
        expected_message_count: Optional[int] = None,
        actual_message_count: Optional[int] = None,
        **kwargs
    ):
        """Initialize feedback cycle error.
        
        Args:
            message: Error message
            cycle_stage: Stage of feedback cycle
            expected_message_count: Expected number of messages
            actual_message_count: Actual number of messages
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        if cycle_stage:
            details["cycle_stage"] = cycle_stage
        if expected_message_count is not None:
            details["expected_message_count"] = expected_message_count
        if actual_message_count is not None:
            details["actual_message_count"] = actual_message_count
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.cycle_stage = cycle_stage
        self.expected_message_count = expected_message_count
        self.actual_message_count = actual_message_count


class TranslationFeedbackError(FeedbackError):
    """Exception raised when translation feedback fails."""
    
    def __init__(
        self,
        message: str,
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        translation_text: Optional[str] = None,
        **kwargs
    ):
        """Initialize translation feedback error.
        
        Args:
            message: Error message
            source_language: Source language for translation
            target_language: Target language for translation
            translation_text: Text being translated
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        if source_language:
            details["source_language"] = source_language
        if target_language:
            details["target_language"] = target_language
        if translation_text:
            details["translation_text"] = translation_text[:200]  # Truncate for safety
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.source_language = source_language
        self.target_language = target_language
        self.translation_text = translation_text


class FeedbackTimingError(FeedbackError):
    """Exception raised when feedback timing is incorrect."""
    
    def __init__(
        self,
        message: str,
        timing_rule: str,
        current_timing: Optional[str] = None,
        expected_timing: Optional[str] = None,
        **kwargs
    ):
        """Initialize feedback timing error.
        
        Args:
            message: Error message
            timing_rule: Timing rule that was violated
            current_timing: Current timing state
            expected_timing: Expected timing state
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        details["timing_rule"] = timing_rule
        if current_timing:
            details["current_timing"] = current_timing
        if expected_timing:
            details["expected_timing"] = expected_timing
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.timing_rule = timing_rule
        self.current_timing = current_timing
        self.expected_timing = expected_timing


class FeedbackContentError(FeedbackError):
    """Exception raised when feedback content is inappropriate or invalid."""
    
    def __init__(
        self,
        message: str,
        content_issue: str,
        problematic_content: Optional[str] = None,
        content_guidelines: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize feedback content error.
        
        Args:
            message: Error message
            content_issue: Description of content issue
            problematic_content: The problematic content
            content_guidelines: Relevant content guidelines
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        details["content_issue"] = content_issue
        if problematic_content:
            details["problematic_content"] = problematic_content[:200]
        if content_guidelines:
            details["content_guidelines"] = content_guidelines
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.content_issue = content_issue
        self.problematic_content = problematic_content
        self.content_guidelines = content_guidelines


class FeedbackLimitError(FeedbackError):
    """Exception raised when feedback limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        limit_type: str,
        current_value: int,
        limit_value: int,
        **kwargs
    ):
        """Initialize feedback limit error.
        
        Args:
            message: Error message
            limit_type: Type of limit exceeded
            current_value: Current value that exceeded limit
            limit_value: The limit that was exceeded
            **kwargs: Additional arguments for FeedbackError
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


class FeedbackParsingError(FeedbackError):
    """Exception raised when feedback parsing fails."""
    
    def __init__(
        self,
        message: str,
        parsing_stage: str,
        raw_feedback: Optional[str] = None,
        expected_format: Optional[str] = None,
        **kwargs
    ):
        """Initialize feedback parsing error.
        
        Args:
            message: Error message
            parsing_stage: Stage where parsing failed
            raw_feedback: Raw feedback that failed to parse
            expected_format: Expected format for feedback
            **kwargs: Additional arguments for FeedbackError
        """
        details = kwargs.get('details', {})
        details["parsing_stage"] = parsing_stage
        if raw_feedback:
            details["raw_feedback"] = raw_feedback[:300]  # Truncate for safety
        if expected_format:
            details["expected_format"] = expected_format
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.parsing_stage = parsing_stage
        self.raw_feedback = raw_feedback
        self.expected_format = expected_format