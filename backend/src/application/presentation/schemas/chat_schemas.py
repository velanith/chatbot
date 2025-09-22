"""Chat API schemas for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid

from src.domain.entities.session import SessionMode, ProficiencyLevel
from src.domain.entities.message import CorrectionCategory
from src.domain.entities.structured_feedback import ExtendedCorrectionCategory


class CorrectionSchema(BaseModel):
    """Schema for correction data."""
    
    original: str = Field(..., description="Original incorrect text")
    correction: str = Field(..., description="Corrected text")
    category: CorrectionCategory = Field(..., description="Type of correction")
    explanation: str = Field(..., description="Explanation of the correction")
    
    class Config:
        use_enum_values = True


class MicroExerciseSchema(BaseModel):
    """Schema for micro-exercise data."""
    
    type: str = Field(..., description="Type of exercise (fill_blank, multiple_choice, etc.)")
    prompt: str = Field(..., description="Exercise prompt/question")
    options: Optional[List[str]] = Field(None, description="Multiple choice options if applicable")
    correct_answer: Optional[str] = Field(None, description="Correct answer for validation")
    explanation: Optional[str] = Field(None, description="Explanation of the answer")


class AlternativeExpressionSchema(BaseModel):
    """Schema for alternative expression suggestions."""
    
    original: str = Field(..., description="Original expression")
    alternative: str = Field(..., description="Alternative expression")
    context: str = Field(..., description="Context for usage")
    formality_level: str = Field(..., description="Formality level (formal, informal, neutral)")
    usage_note: Optional[str] = Field(None, description="Additional usage notes")


class DetailedCorrectionSchema(BaseModel):
    """Schema for detailed correction with examples."""
    
    original: str = Field(..., description="Original incorrect text")
    correction: str = Field(..., description="Corrected text")
    explanation: str = Field(..., description="Explanation of the correction")
    category: ExtendedCorrectionCategory = Field(..., description="Type of correction")
    examples: List[str] = Field(..., description="Usage examples")
    rule_reference: Optional[str] = Field(None, description="Grammar rule reference")
    
    class Config:
        use_enum_values = True


class GrammarFeedbackSchema(BaseModel):
    """Schema for grammar-specific feedback."""
    
    rule_name: str = Field(..., description="Grammar rule name")
    explanation: str = Field(..., description="Rule explanation")
    correct_usage: str = Field(..., description="Correct usage example")
    incorrect_usage: str = Field(..., description="Incorrect usage example")
    additional_examples: List[str] = Field(..., description="Additional examples")
    difficulty_level: str = Field(..., description="Difficulty level (beginner, intermediate, advanced)")


class StructuredFeedbackSchema(BaseModel):
    """Schema for comprehensive structured feedback."""
    
    conversation_continuation: str = Field(..., description="Suggestion for continuing conversation")
    grammar_feedback: Optional[GrammarFeedbackSchema] = Field(None, description="Grammar-specific feedback")
    error_corrections: List[DetailedCorrectionSchema] = Field(default_factory=list, description="Detailed error corrections")
    alternative_expressions: List[AlternativeExpressionSchema] = Field(default_factory=list, description="Alternative expression suggestions")
    native_translation: Optional[str] = Field(None, description="Translation to native language")
    message_count: int = Field(..., description="Number of messages in feedback cycle")
    overall_assessment: str = Field(..., description="Overall assessment of progress")


class TopicSchema(BaseModel):
    """Schema for conversation topic information."""
    
    id: str = Field(..., description="Topic ID")
    name: str = Field(..., description="Topic name")
    description: str = Field(..., description="Topic description")
    category: str = Field(..., description="Topic category")
    difficulty_level: str = Field(..., description="Topic difficulty level")
    keywords: List[str] = Field(default_factory=list, description="Topic keywords")
    conversation_starters: List[str] = Field(default_factory=list, description="Conversation starters")
    related_topics: List[str] = Field(default_factory=list, description="Related topic IDs")


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    
    message: str = Field(
        ..., 
        min_length=1, 
        max_length=1000,
        description="User's message content"
    )
    session_id: Optional[uuid.UUID] = Field(
        None, 
        description="Existing session ID (optional for new conversations)"
    )
    mode: Optional[SessionMode] = Field(
        SessionMode.TUTOR, 
        description="Chat mode: tutor (with corrections) or buddy (natural conversation)"
    )
    level: Optional[ProficiencyLevel] = Field(
        ProficiencyLevel.A2, 
        description="User's English proficiency level"
    )
    native_language: Optional[str] = Field(
        "TR", 
        min_length=2, 
        max_length=5,
        description="User's native language code (ISO 639-1)"
    )
    target_language: Optional[str] = Field(
        "EN", 
        min_length=2, 
        max_length=5,
        description="Target language code (ISO 639-1)"
    )
    
    @field_validator('message')
    @classmethod
    def validate_message_content(cls, v):
        """Validate message content."""
        if not v or v.isspace():
            raise ValueError('Message cannot be empty or only whitespace')
        
        # Basic content filtering
        forbidden_patterns = ['http://', 'https://', '<script', '<iframe']
        v_lower = v.lower()
        for pattern in forbidden_patterns:
            if pattern in v_lower:
                raise ValueError(f'Message contains forbidden content: {pattern}')
        
        return v.strip()
    
    @field_validator('native_language', 'target_language')
    @classmethod
    def validate_language_codes(cls, v):
        """Validate language codes."""
        if v:
            v = v.upper()
            # Basic validation - could be enhanced with ISO 639-1 list
            if len(v) < 2 or len(v) > 5:
                raise ValueError('Language code must be 2-5 characters')
        return v
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "message": "Hello! How are you today?",
                "session_id": None,
                "mode": "tutor",
                "level": "A2",
                "native_language": "TR",
                "target_language": "EN"
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    
    response: str = Field(..., description="AI assistant's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    corrections: List[CorrectionSchema] = Field(
        default_factory=list, 
        description="Grammar/vocabulary corrections (tutor mode only)"
    )
    translation: Optional[str] = Field(
        None, 
        description="Translation of user message to target language (when user writes in native language)"
    )
    micro_exercise: Optional[str] = Field(
        None, 
        description="Optional micro-exercise based on corrections"
    )
    mode: SessionMode = Field(..., description="Current chat mode")
    level: ProficiencyLevel = Field(..., description="Current proficiency level")
    message_count: int = Field(..., description="Total messages in this session")
    response_time_ms: int = Field(..., description="Response generation time in milliseconds")
    
    # Enhanced features
    structured_feedback: Optional[StructuredFeedbackSchema] = Field(
        None, 
        description="Comprehensive structured feedback (provided every 3 messages)"
    )
    current_topic: Optional[TopicSchema] = Field(
        None, 
        description="Current conversation topic information"
    )
    topic_transition_suggestion: Optional[str] = Field(
        None, 
        description="Suggestion for transitioning to a new topic"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    prompt_version: Optional[str] = Field(None, description="AI prompt version used")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "response": "Hello! I'm doing well, thank you. How are you today? That's a great way to start a conversation!",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "corrections": [
                    {
                        "original": "How you today?",
                        "correction": "How are you today?",
                        "category": "grammar",
                        "explanation": "Missing auxiliary verb 'are' in question formation"
                    }
                ],
                "micro_exercise": {
                    "type": "fill_blank",
                    "prompt": "Complete the question: How ___ you today?",
                    "options": ["are", "is", "do"],
                    "correct_answer": "are",
                    "explanation": "Use 'are' with 'you' in questions"
                },
                "mode": "tutor",
                "level": "A2",
                "message_count": 1,
                "response_time_ms": 1500,
                "structured_feedback": {
                    "conversation_continuation": "Great job! Let's continue talking about daily activities.",
                    "grammar_feedback": {
                        "rule_name": "Question Formation",
                        "explanation": "Questions with 'you' require the auxiliary verb 'are'",
                        "correct_usage": "How are you today?",
                        "incorrect_usage": "How you today?",
                        "additional_examples": ["Where are you from?", "What are you doing?"],
                        "difficulty_level": "beginner"
                    },
                    "error_corrections": [],
                    "alternative_expressions": [
                        {
                            "original": "How are you today?",
                            "alternative": "How's your day going?",
                            "context": "Casual greeting",
                            "formality_level": "informal",
                            "usage_note": "More casual and friendly"
                        }
                    ],
                    "native_translation": None,
                    "message_count": 3,
                    "overall_assessment": "Good progress with basic greetings!"
                },
                "current_topic": {
                    "id": "daily_greetings",
                    "name": "Daily Greetings",
                    "description": "Common greetings and how to respond",
                    "category": "daily_life",
                    "difficulty_level": "A1",
                    "keywords": ["hello", "hi", "good morning", "how are you"],
                    "conversation_starters": ["Hello! How are you today?", "Good morning! How's everything?"],
                    "related_topics": ["introductions", "small_talk"]
                },
                "topic_transition_suggestion": None,
                "created_at": "2024-01-15T10:30:00Z",
                "prompt_version": "v1.0"
            }
        }


class ChatErrorResponse(BaseModel):
    """Error response schema for chat endpoint."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID if available")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Message content is required and cannot be empty",
                "details": {
                    "field": "message",
                    "constraint": "min_length"
                },
                "session_id": None,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
# Chatbot Schemas
class ChatbotMessageRequest(BaseModel):
    """Request schema for chatbot messages."""
    
    message: str = Field(..., description="User message to send to chatbot")
    session_id: Optional[str] = Field(None, description="Optional session ID")
    include_history: bool = Field(True, description="Include chat history in request")
    max_history_messages: int = Field(20, description="Maximum number of history messages")


class ChatbotMessageResponse(BaseModel):
    """Response schema for chatbot messages."""
    
    response: str = Field(..., description="Chatbot response")
    session_id: str = Field(..., description="Session ID")
    message_count: int = Field(..., description="Total messages in session")
    timestamp: str = Field(..., description="Response timestamp")
    model_used: str = Field(..., description="AI model used")


class SessionMessageResponse(BaseModel):
    """Schema for session message."""
    
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class SessionCreateRequest(BaseModel):
    """Request schema for creating new session."""
    
    title: Optional[str] = Field(None, description="Session title")


class SessionCreateResponse(BaseModel):
    """Response schema for session creation."""
    
    session_id: str = Field(..., description="Created session ID")
    message: str = Field(..., description="Success message")
    timestamp: str = Field(..., description="Creation timestamp")


# Memory Chat Schemas (from backend integration)
class MemoryChatRequest(BaseModel):
    """Request model for memory-based chat."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    session_id: Optional[str] = Field(None, description="Session ID")


class MemoryChatResponse(BaseModel):
    """Response model for memory-based chat."""
    role: str = Field(..., description="Response role")
    content: str = Field(..., description="Response content")
    session_id: str = Field(..., description="Session ID")
    message_count: Optional[int] = Field(None, description="Total messages in session")
    timestamp: Optional[str] = Field(None, description="Response timestamp")


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str = Field(..., description="Session ID")
    created_at: str = Field(..., description="Session creation timestamp")
    message_count: int = Field(..., description="Number of messages in session")
    last_message: str = Field(..., description="Preview of last message")


# Aliases for backward compatibility
ChatbotRequest = ChatbotMessageRequest
ChatbotResponse = ChatbotMessageResponse
SessionResponse = SessionCreateResponse
MessageResponse = SessionMessageResponse