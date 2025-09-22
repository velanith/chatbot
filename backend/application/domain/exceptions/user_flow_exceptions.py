"""User flow-specific exception classes."""

from typing import Optional, Dict, Any, List
from .base_exceptions import DomainError, ErrorCode


class UserFlowError(DomainError):
    """Base exception for user flow-related errors."""
    
    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        flow_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize user flow error.
        
        Args:
            message: Error message
            user_id: User ID associated with error
            flow_stage: Stage of user flow where error occurred
            details: Additional details
        """
        error_details = details or {}
        if user_id:
            error_details["user_id"] = user_id
        if flow_stage:
            error_details["flow_stage"] = flow_stage
            
        super().__init__(
            message=message,
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            details=error_details
        )
        self.user_id = user_id
        self.flow_stage = flow_stage


class OnboardingError(UserFlowError):
    """Exception raised when user onboarding fails."""
    
    def __init__(
        self,
        message: str,
        onboarding_step: Optional[str] = None,
        completion_percentage: Optional[float] = None,
        **kwargs
    ):
        """Initialize onboarding error.
        
        Args:
            message: Error message
            onboarding_step: Step where onboarding failed
            completion_percentage: Percentage of onboarding completed
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        if onboarding_step:
            details["onboarding_step"] = onboarding_step
        if completion_percentage is not None:
            details["completion_percentage"] = completion_percentage
            
        kwargs['details'] = details
        kwargs['flow_stage'] = "onboarding"
        super().__init__(message, **kwargs)
        self.onboarding_step = onboarding_step
        self.completion_percentage = completion_percentage


class LanguagePreferenceError(UserFlowError):
    """Exception raised when language preference setting fails."""
    
    def __init__(
        self,
        message: str,
        native_language: Optional[str] = None,
        target_language: Optional[str] = None,
        preference_type: Optional[str] = None,
        **kwargs
    ):
        """Initialize language preference error.
        
        Args:
            message: Error message
            native_language: Native language being set
            target_language: Target language being set
            preference_type: Type of preference being set
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        if native_language:
            details["native_language"] = native_language
        if target_language:
            details["target_language"] = target_language
        if preference_type:
            details["preference_type"] = preference_type
            
        kwargs['details'] = details
        kwargs['flow_stage'] = "language_preferences"
        super().__init__(message, **kwargs)
        self.native_language = native_language
        self.target_language = target_language
        self.preference_type = preference_type


class LevelSelectionError(UserFlowError):
    """Exception raised when level selection fails."""
    
    def __init__(
        self,
        message: str,
        selection_method: Optional[str] = None,
        available_levels: Optional[List[str]] = None,
        selected_level: Optional[str] = None,
        **kwargs
    ):
        """Initialize level selection error.
        
        Args:
            message: Error message
            selection_method: Method used for level selection (manual/assessment)
            available_levels: List of available levels
            selected_level: Level that was selected
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        if selection_method:
            details["selection_method"] = selection_method
        if available_levels:
            details["available_levels"] = available_levels
        if selected_level:
            details["selected_level"] = selected_level
            
        kwargs['details'] = details
        kwargs['flow_stage'] = "level_selection"
        super().__init__(message, **kwargs)
        self.selection_method = selection_method
        self.available_levels = available_levels
        self.selected_level = selected_level


class FlowStateError(UserFlowError):
    """Exception raised when user flow state is invalid."""
    
    def __init__(
        self,
        message: str,
        current_state: str,
        expected_state: str,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Initialize flow state error.
        
        Args:
            message: Error message
            current_state: Current flow state
            expected_state: Expected flow state
            operation: Operation that was attempted
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        details.update({
            "current_state": current_state,
            "expected_state": expected_state
        })
        if operation:
            details["operation"] = operation
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.current_state = current_state
        self.expected_state = expected_state
        self.operation = operation


class FlowValidationError(UserFlowError):
    """Exception raised when user flow data validation fails."""
    
    def __init__(
        self,
        message: str,
        validation_field: Optional[str] = None,
        validation_rule: Optional[str] = None,
        provided_value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize flow validation error.
        
        Args:
            message: Error message
            validation_field: Field that failed validation
            validation_rule: Validation rule that failed
            provided_value: Value that was provided
            **kwargs: Additional arguments for UserFlowError
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


class ChatInitializationError(UserFlowError):
    """Exception raised when chat initialization fails."""
    
    def __init__(
        self,
        message: str,
        initialization_stage: Optional[str] = None,
        session_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize chat initialization error.
        
        Args:
            message: Error message
            initialization_stage: Stage where initialization failed
            session_config: Session configuration used
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        if initialization_stage:
            details["initialization_stage"] = initialization_stage
        if session_config:
            details["session_config"] = session_config
            
        kwargs['details'] = details
        kwargs['flow_stage'] = "chat_initialization"
        super().__init__(message, **kwargs)
        self.initialization_stage = initialization_stage
        self.session_config = session_config


class UserPreferenceError(UserFlowError):
    """Exception raised when user preference operations fail."""
    
    def __init__(
        self,
        message: str,
        preference_category: Optional[str] = None,
        preference_key: Optional[str] = None,
        preference_value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize user preference error.
        
        Args:
            message: Error message
            preference_category: Category of preference
            preference_key: Specific preference key
            preference_value: Preference value being set
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        if preference_category:
            details["preference_category"] = preference_category
        if preference_key:
            details["preference_key"] = preference_key
        if preference_value is not None:
            details["preference_value"] = str(preference_value)
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.preference_category = preference_category
        self.preference_key = preference_key
        self.preference_value = preference_value


class FlowTransitionError(UserFlowError):
    """Exception raised when flow transition fails."""
    
    def __init__(
        self,
        message: str,
        from_stage: str,
        to_stage: str,
        transition_reason: Optional[str] = None,
        **kwargs
    ):
        """Initialize flow transition error.
        
        Args:
            message: Error message
            from_stage: Stage being transitioned from
            to_stage: Stage being transitioned to
            transition_reason: Reason for transition
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        details.update({
            "from_stage": from_stage,
            "to_stage": to_stage
        })
        if transition_reason:
            details["transition_reason"] = transition_reason
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.transition_reason = transition_reason


class OnboardingIncompleteError(OnboardingError):
    """Exception raised when onboarding is incomplete for required operation."""
    
    def __init__(
        self,
        required_operation: str,
        missing_steps: List[str],
        message: str = "Onboarding incomplete for operation",
        **kwargs
    ):
        """Initialize onboarding incomplete error.
        
        Args:
            required_operation: Operation that requires complete onboarding
            missing_steps: List of missing onboarding steps
            message: Error message
            **kwargs: Additional arguments for OnboardingError
        """
        details = kwargs.get('details', {})
        details.update({
            "required_operation": required_operation,
            "missing_steps": missing_steps
        })
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.required_operation = required_operation
        self.missing_steps = missing_steps


class InvalidLanguagePairError(LanguagePreferenceError):
    """Exception raised when language pair is invalid for user flow."""
    
    def __init__(
        self,
        native_language: str,
        target_language: str,
        supported_pairs: Optional[List[str]] = None,
        message: str = "Invalid language pair for user flow",
        **kwargs
    ):
        """Initialize invalid language pair error."""
        details = kwargs.get('details', {})
        if supported_pairs:
            details["supported_pairs"] = supported_pairs
            
        kwargs['details'] = details
        super().__init__(
            message=message,
            native_language=native_language,
            target_language=target_language,
            preference_type="language_pair",
            **kwargs
        )
        self.supported_pairs = supported_pairs


class FlowTimeoutError(UserFlowError):
    """Exception raised when user flow times out."""
    
    def __init__(
        self,
        message: str,
        timeout_duration: Optional[int] = None,
        elapsed_time: Optional[int] = None,
        **kwargs
    ):
        """Initialize flow timeout error.
        
        Args:
            message: Error message
            timeout_duration: Timeout duration in seconds
            elapsed_time: Time elapsed before timeout
            **kwargs: Additional arguments for UserFlowError
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


class FlowDataCorruptionError(UserFlowError):
    """Exception raised when user flow data is corrupted."""
    
    def __init__(
        self,
        message: str,
        corrupted_fields: Optional[List[str]] = None,
        recovery_possible: Optional[bool] = None,
        **kwargs
    ):
        """Initialize flow data corruption error.
        
        Args:
            message: Error message
            corrupted_fields: List of corrupted data fields
            recovery_possible: Whether data recovery is possible
            **kwargs: Additional arguments for UserFlowError
        """
        details = kwargs.get('details', {})
        if corrupted_fields:
            details["corrupted_fields"] = corrupted_fields
        if recovery_possible is not None:
            details["recovery_possible"] = recovery_possible
            
        kwargs['details'] = details
        super().__init__(message, **kwargs)
        self.corrupted_fields = corrupted_fields
        self.recovery_possible = recovery_possible