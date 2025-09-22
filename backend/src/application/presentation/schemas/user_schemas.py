"""User API schemas."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

from .common_schemas import (
    BaseResponse, 
    ResponseStatus, 
    TimestampMixin,
    UUIDMixin,
    validate_non_empty_string,
    validate_email_format
)
from .chat_schemas import ProficiencyLevel


class NotificationPreference(str, Enum):
    """Notification preference enumeration."""
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    NONE = "none"


class LearningGoal(str, Enum):
    """Learning goal enumeration."""
    CONVERSATION = "conversation"
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    FLUENCY = "fluency"
    BUSINESS_ENGLISH = "business_english"
    ACADEMIC_ENGLISH = "academic_english"
    TRAVEL_ENGLISH = "travel_english"


class Theme(str, Enum):
    """UI theme enumeration."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class Language(str, Enum):
    """Interface language enumeration."""
    EN = "en"
    TR = "tr"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    RU = "ru"
    ZH = "zh"
    JA = "ja"
    KO = "ko"


class UserPreferencesSchema(BaseModel):
    """User preferences schema."""
    proficiency_level: ProficiencyLevel = Field(..., description="Current proficiency level")
    learning_goals: List[LearningGoal] = Field(default_factory=list, description="Learning goals")
    notification_preferences: List[NotificationPreference] = Field(
        default_factory=list, 
        description="Notification preferences"
    )
    interface_language: Language = Field(Language.EN, description="Interface language")
    theme: Theme = Field(Theme.AUTO, description="UI theme preference")
    daily_goal_minutes: int = Field(30, ge=5, le=180, description="Daily learning goal in minutes")
    correction_level: int = Field(3, ge=1, le=5, description="Correction intensity level (1-5)")
    auto_exercises: bool = Field(True, description="Automatically generate exercises")
    voice_enabled: bool = Field(False, description="Enable voice features")
    timezone: str = Field("UTC", description="User timezone")
    
    @field_validator('learning_goals')
    @classmethod
    def validate_learning_goals(cls, v):
        """Validate learning goals list."""
        if len(v) > 5:
            raise ValueError('Maximum 5 learning goals allowed')
        return v
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "proficiency_level": "A2",
                "learning_goals": ["conversation", "grammar", "vocabulary"],
                "notification_preferences": ["email", "push"],
                "interface_language": "en",
                "theme": "auto",
                "daily_goal_minutes": 30,
                "correction_level": 3,
                "auto_exercises": True,
                "voice_enabled": False,
                "timezone": "America/New_York"
            }
        }


class UserUpdateRequest(BaseModel):
    """User update request schema."""
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    email: Optional[str] = Field(None, description="Email address")
    username: Optional[str] = Field(None, min_length=3, max_length=30, description="Username")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    preferences: Optional[UserPreferencesSchema] = Field(None, description="User preferences")
    
    # Validators
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None:
            return validate_email_format(v)
        return v
    
    @field_validator('first_name', 'last_name', 'bio')
    @classmethod
    def validate_text_fields(cls, v):
        if v is not None:
            return validate_non_empty_string(v)
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "username": "johndoe",
                "bio": "English learner passionate about improving conversation skills",
                "preferences": {
                    "proficiency_level": "B1",
                    "learning_goals": ["conversation", "vocabulary"],
                    "daily_goal_minutes": 45
                }
            }
        }


class UserStatsSchema(BaseModel):
    """User statistics schema."""
    total_sessions: int = Field(..., ge=0, description="Total number of sessions")
    total_messages: int = Field(..., ge=0, description="Total messages sent")
    total_time_minutes: int = Field(..., ge=0, description="Total learning time")
    words_learned: int = Field(..., ge=0, description="Total words learned")
    corrections_received: int = Field(..., ge=0, description="Total corrections received")
    exercises_completed: int = Field(..., ge=0, description="Total exercises completed")
    current_streak: int = Field(..., ge=0, description="Current learning streak in days")
    longest_streak: int = Field(..., ge=0, description="Longest learning streak in days")
    average_accuracy: float = Field(..., ge=0, le=100, description="Average accuracy percentage")
    level_progress: float = Field(..., ge=0, le=100, description="Progress in current level")
    
    class Config:
        schema_extra = {
            "example": {
                "total_sessions": 45,
                "total_messages": 1250,
                "total_time_minutes": 2025,
                "words_learned": 340,
                "corrections_received": 180,
                "exercises_completed": 95,
                "current_streak": 7,
                "longest_streak": 15,
                "average_accuracy": 87.5,
                "level_progress": 65.0
            }
        }


class UserAchievementSchema(BaseModel):
    """User achievement schema."""
    id: str = Field(..., description="Achievement ID")
    name: str = Field(..., description="Achievement name")
    description: str = Field(..., description="Achievement description")
    icon: str = Field(..., description="Achievement icon")
    earned_at: datetime = Field(..., description="When achievement was earned")
    category: str = Field(..., description="Achievement category")
    points: int = Field(..., ge=0, description="Points awarded")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "first_conversation",
                "name": "First Conversation",
                "description": "Completed your first conversation session",
                "icon": "🎉",
                "earned_at": "2024-01-01T12:00:00Z",
                "category": "milestone",
                "points": 50
            }
        }


class UserProfileData(TimestampMixin, UUIDMixin, BaseModel):
    """User profile data schema."""
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    bio: Optional[str] = Field(None, description="User bio")
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: bool = Field(..., description="Whether user email is verified")
    is_premium: bool = Field(False, description="Whether user has premium subscription")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    preferences: UserPreferencesSchema = Field(..., description="User preferences")
    stats: UserStatsSchema = Field(..., description="User statistics")
    achievements: List[UserAchievementSchema] = Field(default_factory=list, description="User achievements")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "bio": "Learning English to improve my career prospects",
                "is_active": True,
                "is_verified": True,
                "is_premium": False,
                "last_login": "2024-01-01T12:00:00Z",
                "preferences": {
                    "proficiency_level": "A2",
                    "learning_goals": ["conversation", "grammar"],
                    "daily_goal_minutes": 30
                },
                "stats": {
                    "total_sessions": 45,
                    "total_messages": 1250,
                    "current_streak": 7,
                    "average_accuracy": 87.5
                },
                "achievements": [
                    {
                        "id": "first_conversation",
                        "name": "First Conversation",
                        "description": "Completed your first conversation",
                        "earned_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class UserResponse(BaseResponse):
    """User response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("User operation completed successfully")
    data: UserProfileData = Field(..., description="User profile data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "User profile retrieved successfully",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True,
                    "is_verified": True
                }
            }
        }


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @model_validator(mode='after')
    def passwords_match(self):
        """Validate that passwords match."""
        if self.new_password and self.confirm_password and self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "OldPassword123",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123"
            }
        }


class EmailChangeRequest(BaseModel):
    """Email change request schema."""
    new_email: str = Field(..., description="New email address")
    password: str = Field(..., description="Current password for verification")
    
    @field_validator('new_email')
    @classmethod
    def validate_new_email(cls, v):
        return validate_email_format(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_non_empty_string(v)
    
    class Config:
        schema_extra = {
            "example": {
                "new_email": "newemail@example.com",
                "password": "CurrentPassword123"
            }
        }


class AccountDeletionRequest(BaseModel):
    """Account deletion request schema."""
    password: str = Field(..., description="Current password for verification")
    confirmation: str = Field(..., description="Confirmation text")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deletion")
    
    @field_validator('confirmation')
    @classmethod
    def validate_confirmation(cls, v):
        """Validate confirmation text."""
        if v.lower() != "delete my account":
            raise ValueError('Confirmation must be "delete my account"')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "password": "CurrentPassword123",
                "confirmation": "delete my account",
                "reason": "No longer need the service"
            }
        }


class UserListItem(TimestampMixin, UUIDMixin, BaseModel):
    """User list item schema (for admin use)."""
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_premium: bool = Field(False, description="Whether user has premium")
    last_login: Optional[datetime] = Field(None, description="Last login")
    total_sessions: int = Field(..., ge=0, description="Total sessions")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": True,
                "is_premium": False,
                "last_login": "2024-01-01T12:00:00Z",
                "total_sessions": 45,
                "created_at": "2024-01-01T10:00:00Z"
            }
        }


class BulkUserOperation(BaseModel):
    """Bulk user operation schema."""
    user_ids: List[str] = Field(..., description="List of user IDs")
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v):
        """Validate user IDs list."""
        if len(v) == 0:
            raise ValueError('At least one user ID is required')
        if len(v) > 100:
            raise ValueError('Maximum 100 user IDs allowed per operation')
        return v
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v):
        """Validate operation type."""
        allowed_operations = ['activate', 'deactivate', 'verify', 'unverify', 'delete']
        if v not in allowed_operations:
            raise ValueError(f'Operation must be one of: {", ".join(allowed_operations)}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174001"
                ],
                "operation": "activate",
                "parameters": {
                    "send_notification": True
                }
            }
        }


class UserSearchRequest(BaseModel):
    """User search request schema."""
    query: Optional[str] = Field(None, description="Search query")
    email: Optional[str] = Field(None, description="Filter by email")
    username: Optional[str] = Field(None, description="Filter by username")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_verified: Optional[bool] = Field(None, description="Filter by verified status")
    is_premium: Optional[bool] = Field(None, description="Filter by premium status")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    last_login_after: Optional[datetime] = Field(None, description="Filter by last login")
    last_login_before: Optional[datetime] = Field(None, description="Filter by last login")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "query": "john",
                "is_active": True,
                "is_verified": True,
                "created_after": "2024-01-01T00:00:00Z"
            }
        }