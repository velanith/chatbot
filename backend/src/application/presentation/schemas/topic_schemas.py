"""Topic management API schemas for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import uuid
from enum import Enum

from .common_schemas import BaseResponse, ResponseStatus


class TopicCategoryEnum(str, Enum):
    """Topic category enumeration for API."""
    DAILY_LIFE = "daily_life"
    TRAVEL = "travel"
    FOOD = "food"
    WORK = "work"
    HOBBIES = "hobbies"
    CULTURE = "culture"
    TECHNOLOGY = "technology"
    HEALTH = "health"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    FAMILY = "family"
    SHOPPING = "shopping"
    WEATHER = "weather"
    NEWS = "news"


class ProficiencyLevelEnum(str, Enum):
    """Proficiency level enumeration for API."""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class TopicSchema(BaseModel):
    """Topic schema for API responses."""
    id: str = Field(..., description="Topic ID")
    name: str = Field(..., description="Topic name")
    description: str = Field(..., description="Topic description")
    category: TopicCategoryEnum = Field(..., description="Topic category")
    difficulty_level: ProficiencyLevelEnum = Field(..., description="Difficulty level")
    keywords: List[str] = Field(default_factory=list, description="Topic keywords")
    conversation_starters: List[str] = Field(default_factory=list, description="Conversation starters")
    related_topics: List[str] = Field(default_factory=list, description="Related topic IDs")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "daily_life_morning_routine",
                "name": "Morning Routine",
                "description": "Discussing daily morning activities and habits",
                "category": "daily_life",
                "difficulty_level": "A2",
                "keywords": ["morning", "routine", "breakfast", "wake up", "habits"],
                "conversation_starters": [
                    "What time do you usually wake up?",
                    "Tell me about your morning routine."
                ],
                "related_topics": ["daily_life_evening_routine", "food_breakfast"]
            }
        }


class TopicSuggestionsRequest(BaseModel):
    """Request schema for topic suggestions."""
    session_id: Optional[uuid.UUID] = Field(None, description="Current session ID for context")
    exclude_recent: Optional[List[str]] = Field(None, description="Recently used topic IDs to exclude")
    limit: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of suggestions")
    category_filter: Optional[List[TopicCategoryEnum]] = Field(None, description="Filter by categories")
    
    @field_validator('exclude_recent')
    @classmethod
    def validate_exclude_recent(cls, v):
        """Validate exclude_recent list."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('exclude_recent must be a list')
            for topic_id in v:
                if not isinstance(topic_id, str) or not topic_id.strip():
                    raise ValueError('All topic IDs must be non-empty strings')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "exclude_recent": ["daily_life_morning_routine", "travel_vacation"],
                "limit": 5,
                "category_filter": ["daily_life", "hobbies"]
            }
        }


class TopicSuggestionsResponse(BaseResponse):
    """Response schema for topic suggestions."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Topic suggestions retrieved successfully")
    suggestions: List[TopicSchema] = Field(..., description="Suggested topics")
    total_available: int = Field(..., description="Total topics available for user level")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Topic suggestions retrieved successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "suggestions": [
                    {
                        "id": "daily_life_morning_routine",
                        "name": "Morning Routine",
                        "description": "Discussing daily morning activities and habits",
                        "category": "daily_life",
                        "difficulty_level": "A2",
                        "keywords": ["morning", "routine", "breakfast"],
                        "conversation_starters": ["What time do you usually wake up?"],
                        "related_topics": ["daily_life_evening_routine"]
                    }
                ],
                "total_available": 25
            }
        }


class TopicSelectionRequest(BaseModel):
    """Request schema for topic selection."""
    topic_id: str = Field(..., description="ID of the topic to select")
    session_id: uuid.UUID = Field(..., description="Session ID to associate with topic")
    
    @field_validator('topic_id')
    @classmethod
    def validate_topic_id(cls, v):
        """Validate topic ID."""
        if not v or not v.strip():
            raise ValueError('Topic ID cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "topic_id": "daily_life_morning_routine",
                "session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class TopicSelectionResponse(BaseResponse):
    """Response schema for topic selection."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Topic selected successfully")
    selected_topic: TopicSchema = Field(..., description="Selected topic details")
    conversation_starter: str = Field(..., description="AI-generated conversation starter")
    related_topics: List[TopicSchema] = Field(default_factory=list, description="Related topics for future reference")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Topic selected successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "selected_topic": {
                    "id": "daily_life_morning_routine",
                    "name": "Morning Routine",
                    "description": "Discussing daily morning activities and habits",
                    "category": "daily_life",
                    "difficulty_level": "A2",
                    "keywords": ["morning", "routine", "breakfast"],
                    "conversation_starters": ["What time do you usually wake up?"],
                    "related_topics": ["daily_life_evening_routine"]
                },
                "conversation_starter": "Good morning! I'd love to hear about your morning routine. What time do you usually wake up, and what's the first thing you do?",
                "related_topics": [
                    {
                        "id": "daily_life_evening_routine",
                        "name": "Evening Routine",
                        "description": "Discussing evening activities and bedtime habits",
                        "category": "daily_life",
                        "difficulty_level": "A2",
                        "keywords": ["evening", "bedtime", "dinner"],
                        "conversation_starters": ["What do you do in the evening?"],
                        "related_topics": ["daily_life_morning_routine"]
                    }
                ]
            }
        }


class CurrentTopicResponse(BaseResponse):
    """Response schema for current session topic."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Current topic retrieved successfully")
    current_topic: Optional[TopicSchema] = Field(None, description="Current topic for the session")
    session_id: uuid.UUID = Field(..., description="Session ID")
    topic_history: List[str] = Field(default_factory=list, description="Previously discussed topic IDs in this session")
    suggested_transitions: List[TopicSchema] = Field(default_factory=list, description="Suggested topic transitions")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Current topic retrieved successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "current_topic": {
                    "id": "daily_life_morning_routine",
                    "name": "Morning Routine",
                    "description": "Discussing daily morning activities and habits",
                    "category": "daily_life",
                    "difficulty_level": "A2",
                    "keywords": ["morning", "routine", "breakfast"],
                    "conversation_starters": ["What time do you usually wake up?"],
                    "related_topics": ["daily_life_evening_routine"]
                },
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "topic_history": ["travel_vacation", "food_breakfast"],
                "suggested_transitions": [
                    {
                        "id": "daily_life_evening_routine",
                        "name": "Evening Routine",
                        "description": "Discussing evening activities and bedtime habits",
                        "category": "daily_life",
                        "difficulty_level": "A2",
                        "keywords": ["evening", "bedtime"],
                        "conversation_starters": ["What do you do in the evening?"],
                        "related_topics": ["daily_life_morning_routine"]
                    }
                ]
            }
        }


class TopicErrorResponse(BaseResponse):
    """Error response schema for topic endpoints."""
    status: ResponseStatus = ResponseStatus.ERROR
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Specific error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "message": "Topic not found",
                "timestamp": "2024-01-01T12:00:00Z",
                "error_code": "TOPIC_NOT_FOUND",
                "details": {
                    "topic_id": "invalid_topic_id"
                }
            }
        }