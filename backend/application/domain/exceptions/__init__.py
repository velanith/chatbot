"""Domain exceptions for business logic errors."""

from .base_exceptions import (
    ErrorCode,
    DomainError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError
)

from .chat_exceptions import (
    ChatError,
    InvalidMessageError,
    SessionNotFoundError,
    MessageProcessingError,
    CorrectionError,
    ExerciseGenerationError
)

from .session_exceptions import (
    SessionError,
    SessionCreationError,
    SessionUpdateError,
    SessionAccessError,
    SessionExpiredError,
    SessionCleanupError
)

from .service_exceptions import (
    ServiceError,
    OpenAIServiceError,
    MemoryManagerError,
    PedagogyEngineError,
    DatabaseError,
    ExternalServiceError,
    TimeoutError,
    ServiceUnavailableError,
    ConfigurationError,
    RetryExhaustedError
)

from .assessment_exceptions import (
    AssessmentError,
    AssessmentNotFoundError,
    AssessmentCreationError,
    AssessmentStateError,
    AssessmentResponseError,
    AssessmentEvaluationError,
    AssessmentCompletionError,
    AssessmentValidationError,
    AssessmentTimeoutError,
    AssessmentLimitError,
    InvalidLanguagePairError,
    AssessmentAlreadyCompletedError,
    AssessmentQuestionGenerationError
)

from .topic_exceptions import (
    TopicError,
    TopicNotFoundError,
    TopicSelectionError,
    TopicSuggestionError,
    TopicValidationError,
    TopicCoherenceError,
    TopicTransitionError,
    TopicStarterGenerationError,
    InvalidTopicCategoryError,
    TopicDifficultyMismatchError,
    TopicDataCorruptionError,
    TopicLimitError,
    TopicCacheError
)

from .feedback_exceptions import (
    FeedbackError,
    FeedbackGenerationError,
    StructuredFeedbackError,
    CorrectionGenerationError,
    GrammarFeedbackError,
    AlternativeExpressionError,
    FeedbackValidationError,
    FeedbackCycleError,
    TranslationFeedbackError,
    FeedbackTimingError,
    FeedbackContentError,
    FeedbackLimitError,
    FeedbackParsingError
)

from .user_flow_exceptions import (
    UserFlowError,
    OnboardingError,
    LanguagePreferenceError,
    LevelSelectionError,
    FlowStateError,
    FlowValidationError,
    ChatInitializationError,
    UserPreferenceError,
    FlowTransitionError,
    OnboardingIncompleteError,
    FlowTimeoutError,
    FlowDataCorruptionError
)

__all__ = [
    # Base exceptions
    "ErrorCode",
    "DomainError",
    "ValidationError", 
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "RateLimitError",
    
    # Chat exceptions
    "ChatError",
    "InvalidMessageError",
    "SessionNotFoundError", 
    "MessageProcessingError",
    "CorrectionError",
    "ExerciseGenerationError",
    
    # Session exceptions
    "SessionError",
    "SessionCreationError",
    "SessionUpdateError",
    "SessionAccessError",
    "SessionExpiredError",
    "SessionCleanupError",
    
    # Service exceptions
    "ServiceError",
    "OpenAIServiceError",
    "MemoryManagerError",
    "PedagogyEngineError",
    "DatabaseError",
    "ExternalServiceError",
    "TimeoutError",
    "ServiceUnavailableError",
    "ConfigurationError",
    "RetryExhaustedError",
    
    # Assessment exceptions
    "AssessmentError",
    "AssessmentNotFoundError",
    "AssessmentCreationError",
    "AssessmentStateError",
    "AssessmentResponseError",
    "AssessmentEvaluationError",
    "AssessmentCompletionError",
    "AssessmentValidationError",
    "AssessmentTimeoutError",
    "AssessmentLimitError",
    "InvalidLanguagePairError",
    "AssessmentAlreadyCompletedError",
    "AssessmentQuestionGenerationError",
    
    # Topic exceptions
    "TopicError",
    "TopicNotFoundError",
    "TopicSelectionError",
    "TopicSuggestionError",
    "TopicValidationError",
    "TopicCoherenceError",
    "TopicTransitionError",
    "TopicStarterGenerationError",
    "InvalidTopicCategoryError",
    "TopicDifficultyMismatchError",
    "TopicDataCorruptionError",
    "TopicLimitError",
    "TopicCacheError",
    
    # Feedback exceptions
    "FeedbackError",
    "FeedbackGenerationError",
    "StructuredFeedbackError",
    "CorrectionGenerationError",
    "GrammarFeedbackError",
    "AlternativeExpressionError",
    "FeedbackValidationError",
    "FeedbackCycleError",
    "TranslationFeedbackError",
    "FeedbackTimingError",
    "FeedbackContentError",
    "FeedbackLimitError",
    "FeedbackParsingError",
    
    # User flow exceptions
    "UserFlowError",
    "OnboardingError",
    "LanguagePreferenceError",
    "LevelSelectionError",
    "FlowStateError",
    "FlowValidationError",
    "ChatInitializationError",
    "UserPreferenceError",
    "FlowTransitionError",
    "OnboardingIncompleteError",
    "FlowTimeoutError",
    "FlowDataCorruptionError"
]