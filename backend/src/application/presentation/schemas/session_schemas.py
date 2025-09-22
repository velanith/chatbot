"""Session API schemas for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import uuid

from src.domain.entities.session import SessionMode, ProficiencyLevel


class SessionRequest(BaseModel):
    """Request schema for session creation."""
    
    mode: SessionMode = Field(..., description="Chat mode: tutor or buddy")
    level: ProficiencyLevel = Field(..., description="User's English proficiency level")
    native_language: Optional[str] = Field(
        "TR", 
        min_length=2, 
        max_length=5,
        description="User's native language code"
    )
    target_language: Optional[str] = Field(
        "EN", 
        min_length=2, 
        max_length=5,
        description="Target language code"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional session metadata"
    )
    
    @field_validator('native_language', 'target_language')
    @classmethod
    def validate_language_codes(cls, v):
        """Validate language codes."""
        if v:
            v = v.upper()
            if len(v) < 2 or len(v) > 5:
                raise ValueError('Language code must be 2-5 characters')
        return v
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "mode": "tutor",
                "level": "A2",
                "native_language": "TR",
                "target_language": "EN",
                "metadata": {
                    "learning_goals": ["grammar", "vocabulary"],
                    "preferred_topics": ["daily_life", "travel"]
                }
            }
        }


class SessionResponse(BaseModel):
    """Response schema for session creation."""
    
    session_id: uuid.UUID = Field(..., description="Created session ID")
    mode: SessionMode = Field(..., description="Session mode")
    level: ProficiencyLevel = Field(..., description="Proficiency level")
    created_at: datetime = Field(..., description="Session creation timestamp")
    is_active: bool = Field(True, description="Whether session is active")
    message_count: int = Field(0, description="Number of messages in session")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "mode": "tutor",
                "level": "A2",
                "created_at": "2024-01-15T10:30:00Z",
                "is_active": True,
                "message_count": 0
            }
        }


class SessionInfoResponse(BaseModel):
    """Detailed session information response."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    user_id: uuid.UUID = Field(..., description="User ID")
    mode: SessionMode = Field(..., description="Session mode")
    level: ProficiencyLevel = Field(..., description="Proficiency level")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Total messages in session")
    duration_minutes: int = Field(..., description="Session duration in minutes")
    is_active: bool = Field(..., description="Whether session is active")
    
    # Optional detailed information
    conversation_summary: Optional[str] = Field(None, description="AI-generated conversation summary")
    recent_topics: List[str] = Field(default_factory=list, description="Recent conversation topics")
    learning_progress: Dict[str, Any] = Field(default_factory=dict, description="Learning progress metrics")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43d1-9f4e-123456789abc",
                "mode": "tutor",
                "level": "A2",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T11:15:00Z",
                "message_count": 15,
                "duration_minutes": 45,
                "is_active": True,
                "conversation_summary": "Discussion about daily routines and hobbies with focus on present tense usage",
                "recent_topics": ["morning_routine", "hobbies", "weekend_plans"],
                "learning_progress": {
                    "total_corrections": 8,
                    "correction_categories": {"grammar": 5, "vocabulary": 3},
                    "correction_rate": 0.53
                }
            }
        }


class SessionListItem(BaseModel):
    """Session list item for session listing."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    mode: SessionMode = Field(..., description="Session mode")
    level: ProficiencyLevel = Field(..., description="Proficiency level")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Number of messages")
    duration_minutes: int = Field(..., description="Session duration in minutes")
    is_active: bool = Field(..., description="Whether session is active")
    preview_text: Optional[str] = Field(None, description="Preview of last message")
    
    class Config:
        use_enum_values = True


class SessionListResponse(BaseModel):
    """Response schema for session listing."""
    
    sessions: List[SessionListItem] = Field(..., description="List of user sessions")
    total_count: int = Field(..., description="Total number of sessions")
    active_count: int = Field(..., description="Number of active sessions")
    
    class Config:
        schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "123e4567-e89b-12d3-a456-426614174000",
                        "mode": "tutor",
                        "level": "A2",
                        "created_at": "2024-01-15T10:30:00Z",
                        "last_activity": "2024-01-15T11:15:00Z",
                        "message_count": 15,
                        "duration_minutes": 45,
                        "is_active": True,
                        "preview_text": "Thank you for the lesson today!"
                    }
                ],
                "total_count": 5,
                "active_count": 2
            }
        }


class SessionUpdateRequest(BaseModel):
    """Request schema for session updates."""
    
    mode: Optional[SessionMode] = Field(None, description="New session mode")
    level: Optional[ProficiencyLevel] = Field(None, description="New proficiency level")
    
    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """Ensure at least one field is provided for update."""
        if self.mode is None and self.level is None:
            raise ValueError('At least one field must be provided for update')
        return self
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "mode": "buddy",
                "level": "B1"
            }
        }


class SessionEndResponse(BaseModel):
    """Response schema for session ending."""
    
    session_id: uuid.UUID = Field(..., description="Ended session ID")
    duration_minutes: int = Field(..., description="Total session duration")
    message_count: int = Field(..., description="Total messages exchanged")
    mode: SessionMode = Field(..., description="Session mode")
    level: ProficiencyLevel = Field(..., description="Proficiency level")
    conversation_summary: Optional[str] = Field(None, description="Final conversation summary")
    learning_progress: Dict[str, Any] = Field(default_factory=dict, description="Learning progress summary")
    ended_at: datetime = Field(..., description="Session end timestamp")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "duration_minutes": 45,
                "message_count": 15,
                "mode": "tutor",
                "level": "A2",
                "conversation_summary": "Great practice session focusing on daily routines and present tense",
                "learning_progress": {
                    "total_corrections": 8,
                    "correction_categories": {"grammar": 5, "vocabulary": 3},
                    "improvement_areas": ["article_usage", "verb_forms"]
                },
                "ended_at": "2024-01-15T11:15:00Z"
            }
        }


class SessionErrorResponse(BaseModel):
    """Error response schema for session endpoints."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID if available")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "session_not_found",
                "message": "Session not found or access denied",
                "details": {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "987fcdeb-51a2-43d1-9f4e-123456789abc"
                },
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class MessageItem(BaseModel):
    """Message item for history response."""
    
    message_id: uuid.UUID = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    corrections: List[Dict[str, Any]] = Field(default_factory=list, description="Corrections made")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional message metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "456e7890-e89b-12d3-a456-426614174001",
                "role": "user",
                "content": "I go to work every days.",
                "timestamp": "2024-01-15T10:35:00Z",
                "corrections": [
                    {
                        "type": "grammar",
                        "original": "every days",
                        "correction": "every day",
                        "explanation": "Use singular 'day' with 'every'"
                    }
                ],
                "metadata": {
                    "response_time_ms": 1250,
                    "confidence_score": 0.85
                }
            }
        }


class SessionHistoryResponse(BaseModel):
    """Response schema for session history."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    messages: List[MessageItem] = Field(..., description="List of messages")
    total_messages: int = Field(..., description="Total number of messages in session")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of messages per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    session_info: SessionInfoResponse = Field(..., description="Session information")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "messages": [
                    {
                        "message_id": "456e7890-e89b-12d3-a456-426614174001",
                        "role": "user",
                        "content": "Hello, I want to practice English.",
                        "timestamp": "2024-01-15T10:30:00Z",
                        "corrections": [],
                        "metadata": {}
                    }
                ],
                "total_messages": 15,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
                "session_info": {
                    "session_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "987fcdeb-51a2-43d1-9f4e-123456789abc",
                    "mode": "tutor",
                    "level": "A2",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T11:15:00Z",
                    "message_count": 15,
                    "duration_minutes": 45,
                    "is_active": True
                }
            }
        }


class ConversationExportResponse(BaseModel):
    """Response schema for conversation export."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    format: str = Field(..., description="Export format")
    data: str = Field(..., description="Exported conversation data")
    metadata: Dict[str, Any] = Field(..., description="Export metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Export generation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "format": "json",
                "data": "{\"session_id\": \"123e4567-e89b-12d3-a456-426614174000\", \"messages\": [...]}",
                "metadata": {
                    "total_messages": 15,
                    "export_size_bytes": 2048,
                    "session_duration_minutes": 45,
                    "mode": "tutor",
                    "level": "A2"
                },
                "generated_at": "2024-01-15T12:00:00Z"
            }
        }