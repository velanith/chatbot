"""Domain entities for the user registration system."""

from .user import User
from .password import Password
from .user_token import UserToken
from .session import Session, SessionMode, ProficiencyLevel
from .message import Message, MessageRole, Correction, CorrectionCategory
from .conversation_context import ConversationContext, UserPreferences
from .validators import DomainValidator, ValidationError
from .assessment import AssessmentSession, AssessmentResponse, AssessmentStatus, LanguagePair
from .topic import Topic, TopicCategory
from .language_preferences import LanguagePreferences
from .structured_feedback import (
    StructuredFeedback, 
    DetailedCorrection, 
    AlternativeExpression, 
    GrammarFeedback, 
    ExtendedCorrectionCategory
)

__all__ = [
    'User', 'Password', 'UserToken',
    'Session', 'SessionMode', 'ProficiencyLevel',
    'Message', 'MessageRole', 'Correction', 'CorrectionCategory',
    'ConversationContext', 'UserPreferences',
    'DomainValidator', 'ValidationError',
    'AssessmentSession', 'AssessmentResponse', 'AssessmentStatus', 'LanguagePair',
    'Topic', 'TopicCategory', 'LanguagePreferences',
    'StructuredFeedback', 'DetailedCorrection', 'AlternativeExpression', 
    'GrammarFeedback', 'ExtendedCorrectionCategory'
]