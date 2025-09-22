"""User flow management API schemas."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from .common_schemas import BaseResponse, ResponseStatus, TimestampMixin
from .chat_schemas import ProficiencyLevel


class FlowState(str, Enum):
    """User flow states."""
    LANGUAGE_SELECTION = "language_selection"
    LEVEL_SELECTION = "level_selection"
    TOPIC_PREFERENCES = "topic_preferences"
    READY_FOR_CHAT = "ready_for_chat"
    ONBOARDING_COMPLETE = "onboarding_complete"


class LanguageOption(BaseModel):
    """Language option schema."""
    code: str = Field(..., description="Language code (ISO 639-1)")
    name: str = Field(..., description="Language name")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "EN",
                "name": "English"
            }
        }


class LevelOption(BaseModel):
    """Level option schema."""
    code: str = Field(..., description="Level code")
    name: str = Field(..., description="Level name")
    description: str = Field(..., description="Level description")
    
    class Config:
        schema_extra = {
            "example": {
                "code": "A2",
                "name": "Elementary (A2)",
                "description": "Simple conversations about familiar topics"
            }
        }


class UserFlowStateData(BaseModel):
    """User flow state data schema."""
    user_id: str = Field(..., description="User ID")
    current_state: FlowState = Field(..., description="Current flow state")
    has_language_preferences: bool = Field(..., description="Whether user has set language preferences")
    has_level_assessment: bool = Field(..., description="Whether user has completed level assessment")
    has_topic_preferences: bool = Field(..., description="Whether user has set topic preferences")
    onboarding_completed: bool = Field(..., description="Whether onboarding is completed")
    next_action: str = Field(..., description="Description of next required action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "current_state": "language_selection",
                "has_language_preferences": False,
                "has_level_assessment": False,
                "has_topic_preferences": False,
                "onboarding_completed": False,
                "next_action": "Please select your native and target languages",
                "metadata": {
                    "native_language": None,
                    "target_language": None,
                    "proficiency_level": None
                }
            }
        }


class LanguagePreferencesRequest(BaseModel):
    """Language preferences request schema."""
    native_language: str = Field(..., min_length=2, max_length=3, description="Native language code")
    target_language: str = Field(..., min_length=2, max_length=3, description="Target language code")
    
    @field_validator('native_language', 'target_language')
    @classmethod
    def validate_language_codes(cls, v):
        """Validate language codes."""
        if not v or len(v) < 2:
            raise ValueError('Language code must be at least 2 characters')
        return v.upper()
    
    @field_validator('target_language')
    @classmethod
    def validate_different_languages(cls, v, info):
        """Validate that target language is different from native language."""
        if 'native_language' in info.data and v.upper() == info.data['native_language'].upper():
            raise ValueError('Target language must be different from native language')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "native_language": "TR",
                "target_language": "EN"
            }
        }


class LevelSelectionOptionsData(BaseModel):
    """Level selection options data schema."""
    assessment_available: bool = Field(..., description="Whether level assessment is available")
    manual_selection_available: bool = Field(..., description="Whether manual level selection is available")
    available_levels: List[LevelOption] = Field(..., description="Available proficiency levels")
    current_level: Optional[str] = Field(None, description="Current proficiency level")
    assessed_level: Optional[str] = Field(None, description="AI-assessed proficiency level")
    assessment_date: Optional[datetime] = Field(None, description="Date of last assessment")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "assessment_available": True,
                "manual_selection_available": True,
                "available_levels": [
                    {
                        "code": "A1",
                        "name": "Beginner (A1)",
                        "description": "Basic phrases and simple interactions"
                    },
                    {
                        "code": "A2",
                        "name": "Elementary (A2)",
                        "description": "Simple conversations about familiar topics"
                    }
                ],
                "current_level": "A2",
                "assessed_level": None,
                "assessment_date": None
            }
        }


class UserFlowStateResponse(BaseResponse):
    """User flow state response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("User flow state retrieved successfully")
    data: UserFlowStateData = Field(..., description="User flow state data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "User flow state retrieved successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "current_state": "language_selection",
                    "has_language_preferences": False,
                    "has_level_assessment": False,
                    "has_topic_preferences": False,
                    "onboarding_completed": False,
                    "next_action": "Please select your native and target languages"
                }
            }
        }


class LanguagePreferencesResponse(BaseResponse):
    """Language preferences response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Language preferences updated successfully")
    data: UserFlowStateData = Field(..., description="Updated user flow state")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Language preferences updated successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "current_state": "level_selection",
                    "has_language_preferences": True,
                    "has_level_assessment": False,
                    "has_topic_preferences": False,
                    "onboarding_completed": False,
                    "next_action": "Please take a level assessment or select your proficiency level"
                }
            }
        }


class LevelSelectionOptionsResponse(BaseResponse):
    """Level selection options response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Level selection options retrieved successfully")
    data: LevelSelectionOptionsData = Field(..., description="Level selection options")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Level selection options retrieved successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "assessment_available": True,
                    "manual_selection_available": True,
                    "available_levels": [
                        {
                            "code": "A1",
                            "name": "Beginner (A1)",
                            "description": "Basic phrases and simple interactions"
                        }
                    ],
                    "current_level": "A2"
                }
            }
        }