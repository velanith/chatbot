"""Authentication API schemas."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr

from .common_schemas import (
    BaseResponse, 
    ResponseStatus, 
    TimestampMixin,
    validate_non_empty_string,
    validate_email_format,
    validate_password_strength,
    validate_username_format
)
from .chat_schemas import ProficiencyLevel


class RegisterRequest(BaseModel):
    """User registration request schema."""
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=30, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    terms_accepted: bool = Field(..., description="Terms and conditions acceptance")
    marketing_consent: bool = Field(False, description="Marketing communications consent")
    
    # Polyglot language learning specific fields
    native_language: str = Field(..., description="User's native language (ISO 639-1 code)")
    target_language: str = Field(..., description="Language user wants to learn (ISO 639-1 code)")
    proficiency_level: ProficiencyLevel = Field(..., description="Current proficiency level in target language")
    
    # Validators
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        return validate_username_format(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(v)
    
    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v):
        if v is not None:
            return validate_non_empty_string(v)
        return v
    
    @model_validator(mode='after')
    def passwords_match(self):
        """Validate that passwords match."""
        if self.password and self.confirm_password and self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
    
    @field_validator('terms_accepted')
    @classmethod
    def terms_must_be_accepted(cls, v):
        """Validate that terms are accepted."""
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v
    
    @field_validator('native_language', 'target_language')
    @classmethod
    def validate_language_codes(cls, v):
        """Validate language codes."""
        # Common language codes - in production this should be more comprehensive
        valid_languages = {
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 
            'ar', 'hi', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi', 'he'
        }
        if v.lower() not in valid_languages:
            raise ValueError(f'Invalid language code: {v}')
        return v.lower()
    
    @model_validator(mode='after')
    def different_languages(self):
        """Validate that target language is different from native language."""
        if self.native_language and self.target_language and self.native_language.lower() == self.target_language.lower():
            raise ValueError('Target language must be different from native language')
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
                "first_name": "John",
                "last_name": "Doe",
                "terms_accepted": True,
                "marketing_consent": False,
                "native_language": "tr",
                "target_language": "en",
                "proficiency_level": "A2"
            }
        }


class LoginRequest(BaseModel):
    """User login request schema."""
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Remember login for extended period")
    
    @field_validator('username_or_email')
    @classmethod
    def validate_username_or_email(cls, v):
        return validate_non_empty_string(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_non_empty_string(v)
    
    class Config:
        schema_extra = {
            "example": {
                "username_or_email": "user@example.com",
                "password": "SecurePass123",
                "remember_me": False
            }
        }


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str = Field(..., description="Refresh token")
    
    @field_validator('refresh_token')
    @classmethod
    def validate_refresh_token(cls, v):
        return validate_non_empty_string(v)
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class TokenData(BaseModel):
    """Token data schema."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    scope: Optional[str] = Field(None, description="Token scope")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": "2024-01-01T12:00:00Z",
                "scope": "read write"
            }
        }


class UserProfile(TimestampMixin, BaseModel):
    """User profile schema."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    is_active: bool = Field(..., description="Whether user account is active")
    is_verified: bool = Field(..., description="Whether user email is verified")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    
    # Language learning specific fields
    native_language: str = Field(..., description="User's native language")
    target_language: str = Field(..., description="Language user is learning")
    proficiency_level: ProficiencyLevel = Field(..., description="Current proficiency level")
    
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
                "last_login": "2024-01-01T12:00:00Z",
                "profile_picture_url": "https://example.com/avatar.jpg",
                "native_language": "tr",
                "target_language": "en",
                "proficiency_level": "A2",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T11:00:00Z"
            }
        }


class TokenResponse(BaseResponse):
    """Token response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Authentication successful")
    data: TokenData = Field(..., description="Token data")
    user: UserProfile = Field(..., description="User profile")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Authentication successful",
                "timestamp": "2024-01-01T12:00:00Z",
                "data": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "expires_at": "2024-01-01T13:00:00Z"
                },
                "user": {
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


class LoginResponse(TokenResponse):
    """Login response schema."""
    message: str = Field("Login successful")


class RegisterResponse(BaseResponse):
    """Registration response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Registration successful")
    user: UserProfile = Field(..., description="Created user profile")
    verification_required: bool = Field(True, description="Whether email verification is required")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Registration successful",
                "timestamp": "2024-01-01T12:00:00Z",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True,
                    "is_verified": False
                },
                "verification_required": True
            }
        }


class LogoutRequest(BaseModel):
    """Logout request schema."""
    refresh_token: Optional[str] = Field(None, description="Refresh token to invalidate")
    logout_all_devices: bool = Field(False, description="Logout from all devices")
    
    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "logout_all_devices": False
            }
        }


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: str = Field(..., description="User email address")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        return validate_password_strength(v)
    
    @model_validator(mode='after')
    def passwords_match(self):
        """Validate that passwords match."""
        if self.new_password and self.confirm_password and self.new_password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "token": "reset-token-123",
                "new_password": "NewSecurePass123",
                "confirm_password": "NewSecurePass123"
            }
        }


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    token: str = Field(..., description="Email verification token")
    
    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        return validate_non_empty_string(v)
    
    class Config:
        schema_extra = {
            "example": {
                "token": "verification-token-123"
            }
        }


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema."""
    email: str = Field(..., description="User email address")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }