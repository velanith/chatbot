"""Common API schemas used across endpoints."""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ResponseStatus(str, Enum):
    """Response status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ErrorType(str, Enum):
    """Error type enumeration."""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    CONFLICT_ERROR = "conflict_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"


class BaseResponse(BaseModel):
    """Base response schema."""
    status: ResponseStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseResponse):
    """Success response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = Field("Operation completed successfully")
    data: Optional[Dict[str, Any]] = None


class ErrorDetail(BaseModel):
    """Error detail schema."""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseResponse):
    """Error response schema."""
    status: ResponseStatus = ResponseStatus.ERROR
    error_type: ErrorType
    message: str = Field(..., description="Main error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information (dev only)")
    
    @field_validator('debug_info', mode='before')
    @classmethod
    def serialize_debug_info(cls, v):
        """Ensure debug_info is serializable."""
        if v is None:
            return v
        
        def make_serializable(obj):
            """Recursively make objects serializable."""
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj
            else:
                # Convert any other type to string
                return str(obj)
        
        return make_serializable(v)


class PaginationMeta(BaseModel):
    """Pagination metadata schema."""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    @field_validator('total_pages', mode='before')
    @classmethod
    def calculate_total_pages(cls, v, info):
        """Calculate total pages based on total items and per page."""
        if info.data and 'total_items' in info.data and 'per_page' in info.data:
            per_page = info.data['per_page']
            total_items = info.data['total_items']
            return (total_items + per_page - 1) // per_page if per_page > 0 else 0
        return v
    
    @field_validator('has_next', mode='before')
    @classmethod
    def calculate_has_next(cls, v, info):
        """Calculate if there is a next page."""
        if info.data and 'page' in info.data and 'total_pages' in info.data:
            return info.data['page'] < info.data['total_pages']
        return v
    
    @field_validator('has_prev', mode='before')
    @classmethod
    def calculate_has_prev(cls, v, info):
        """Calculate if there is a previous page."""
        if info.data and 'page' in info.data:
            return info.data['page'] > 1
        return v


class PaginationResponse(BaseResponse):
    """Paginated response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: List[Any] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class HealthStatus(str, Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ServiceHealth(BaseModel):
    """Individual service health schema."""
    name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Service health status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    last_check: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthResponse(BaseResponse):
    """Health check response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    overall_status: HealthStatus = Field(..., description="Overall system health")
    services: List[ServiceHealth] = Field(..., description="Individual service health")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    version: str = Field(..., description="Application version")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationErrorDetail(ErrorDetail):
    """Validation error detail schema."""
    field: str = Field(..., description="Field that failed validation")
    rejected_value: Any = Field(None, description="Value that was rejected")
    constraint: Optional[str] = Field(None, description="Validation constraint that failed")


class RateLimitInfo(BaseModel):
    """Rate limit information schema."""
    limit: int = Field(..., description="Rate limit threshold")
    remaining: int = Field(..., description="Remaining requests")
    reset_time: datetime = Field(..., description="When the rate limit resets")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying")


class APIMetadata(BaseModel):
    """API metadata schema."""
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment (dev, staging, prod)")
    build_time: datetime = Field(..., description="Build timestamp")
    commit_hash: Optional[str] = Field(None, description="Git commit hash")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Request validation mixins
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UUIDMixin(BaseModel):
    """Mixin for UUID fields."""
    id: Optional[str] = Field(None, description="Unique identifier", pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


# Custom validators
def validate_non_empty_string(v: str) -> str:
    """Validate that string is not empty after stripping."""
    if not v or not v.strip():
        raise ValueError('String cannot be empty')
    return v.strip()


def validate_email_format(v: str) -> str:
    """Validate email format."""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, v):
        raise ValueError('Invalid email format')
    return v.lower()


def validate_password_strength(v: str) -> str:
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


def validate_username_format(v: str) -> str:
    """Validate username format."""
    import re
    if len(v) < 3 or len(v) > 30:
        raise ValueError('Username must be between 3 and 30 characters')
    if not re.match(r'^[a-zA-Z0-9_-]+$', v):
        raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
    return v.lower()