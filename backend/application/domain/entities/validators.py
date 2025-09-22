"""Domain validation utilities."""

import re
import uuid
from typing import Any, List, Optional
from datetime import datetime

from .session import SessionMode, ProficiencyLevel


class ValidationError(ValueError):
    """Custom validation error for domain entities."""
    pass


def validate_uuid(value: Any, field_name: str) -> uuid.UUID:
    """Validate and convert UUID value."""
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValidationError(f"{field_name} must be a valid UUID")
    raise ValidationError(f"{field_name} must be a UUID")


def validate_session_mode(value: Any) -> SessionMode:
    """Validate and convert session mode."""
    if isinstance(value, SessionMode):
        return value
    if isinstance(value, str):
        try:
            return SessionMode(value.lower())
        except ValueError:
            raise ValidationError(f"Invalid session mode: {value}. Must be one of: {[m.value for m in SessionMode]}")
    raise ValidationError("Session mode must be a SessionMode enum or string")


def validate_proficiency_level(value: Any) -> ProficiencyLevel:
    """Validate and convert proficiency level."""
    if isinstance(value, ProficiencyLevel):
        return value
    if isinstance(value, str):
        # Try lowercase first (for beginner, intermediate, etc.)
        try:
            return ProficiencyLevel(value.lower())
        except ValueError:
            # Try uppercase (for A1, A2, etc.)
            try:
                return ProficiencyLevel(value.upper())
            except ValueError:
                raise ValidationError(f"Invalid proficiency level: {value}. Must be one of: {[l.value for l in ProficiencyLevel]}")
    raise ValidationError("Proficiency level must be a ProficiencyLevel enum or string")


def validate_language_code(value: Any, field_name: str) -> str:
    """Validate language code format."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    cleaned = value.strip().upper()
    if len(cleaned) < 2 or len(cleaned) > 5:
        raise ValidationError(f"{field_name} must be 2-5 characters long")
    
    # Basic language code pattern (ISO 639-1 or similar)
    if not re.match(r'^[A-Z]{2,3}(-[A-Z]{2})?$', cleaned):
        raise ValidationError(f"{field_name} must be a valid language code (e.g., 'EN', 'TR', 'EN-US')")
    
    return cleaned


def validate_text_content(value: Any, field_name: str, min_length: int = 1, max_length: int = 5000) -> str:
    """Validate text content with length constraints."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    cleaned = value.strip()
    if len(cleaned) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long")
    
    if len(cleaned) > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
    
    return cleaned


def validate_datetime(value: Any, field_name: str) -> datetime:
    """Validate datetime value."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ValidationError(f"{field_name} must be a valid datetime")
    raise ValidationError(f"{field_name} must be a datetime object")


def validate_list_of_type(value: Any, field_name: str, expected_type: type, max_items: Optional[int] = None) -> List[Any]:
    """Validate list contains only items of expected type."""
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list")
    
    if max_items is not None and len(value) > max_items:
        raise ValidationError(f"{field_name} cannot contain more than {max_items} items")
    
    for i, item in enumerate(value):
        if not isinstance(item, expected_type):
            raise ValidationError(f"{field_name}[{i}] must be of type {expected_type.__name__}")
    
    return value


def validate_optional_string(value: Any, field_name: str, max_length: int = 1000) -> Optional[str]:
    """Validate optional string field."""
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string or None")
    
    cleaned = value.strip()
    if len(cleaned) == 0:
        return None
    
    if len(cleaned) > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
    
    return cleaned


def validate_boolean(value: Any, field_name: str) -> bool:
    """Validate boolean value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ('true', '1', 'yes', 'on'):
            return True
        if value.lower() in ('false', '0', 'no', 'off'):
            return False
    if isinstance(value, int):
        return bool(value)
    
    raise ValidationError(f"{field_name} must be a boolean value")


def validate_required_string(value: Any, field_name: str) -> str:
    """Validate required string field."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"{field_name} cannot be empty")
    
    return cleaned


def validate_enum_value(value: Any, enum_class: type, field_name: str) -> Any:
    """Validate enum value."""
    if isinstance(value, enum_class):
        return value
    
    if isinstance(value, str):
        try:
            return enum_class(value)
        except ValueError:
            valid_values = [e.value for e in enum_class]
            raise ValidationError(f"{field_name} must be one of: {valid_values}")
    
    raise ValidationError(f"{field_name} must be a {enum_class.__name__} enum")


class DomainValidator:
    """Centralized domain validation utilities."""
    
    @staticmethod
    def validate_session_data(data: dict) -> dict:
        """Validate session creation data."""
        validated = {}
        
        if 'id' in data:
            validated['id'] = validate_uuid(data['id'], 'id')
        if 'user_id' in data:
            validated['user_id'] = validate_uuid(data['user_id'], 'user_id')
        if 'mode' in data:
            validated['mode'] = validate_session_mode(data['mode'])
        if 'level' in data:
            validated['level'] = validate_proficiency_level(data['level'])
        if 'created_at' in data:
            validated['created_at'] = validate_datetime(data['created_at'], 'created_at')
        if 'updated_at' in data:
            validated['updated_at'] = validate_datetime(data['updated_at'], 'updated_at')
        if 'is_active' in data:
            validated['is_active'] = validate_boolean(data['is_active'], 'is_active')
        if 'summary' in data:
            validated['summary'] = validate_optional_string(data['summary'], 'summary', 1000)
        
        return validated
    
    @staticmethod
    def validate_user_preferences_data(data: dict) -> dict:
        """Validate user preferences data."""
        validated = {}
        
        if 'native_language' in data:
            validated['native_language'] = validate_language_code(data['native_language'], 'native_language')
        if 'target_language' in data:
            validated['target_language'] = validate_language_code(data['target_language'], 'target_language')
        if 'proficiency_level' in data:
            validated['proficiency_level'] = validate_proficiency_level(data['proficiency_level'])
        
        # Ensure languages are different
        if ('native_language' in validated and 'target_language' in validated and 
            validated['native_language'] == validated['target_language']):
            raise ValidationError("Native and target languages cannot be the same")
        
        return validated
    
    @staticmethod
    def validate_message_data(data: dict) -> dict:
        """Validate message creation data."""
        validated = {}
        
        if 'id' in data:
            validated['id'] = validate_uuid(data['id'], 'id')
        if 'session_id' in data:
            validated['session_id'] = validate_uuid(data['session_id'], 'session_id')
        if 'role' in data:
            if isinstance(data['role'], str):
                try:
                    from .message import MessageRole
                    validated['role'] = MessageRole(data['role'].lower())
                except ValueError:
                    raise ValidationError(f"Invalid message role: {data['role']}")
            else:
                validated['role'] = data['role']
        if 'content' in data:
            validated['content'] = validate_text_content(data['content'], 'content', 1, 5000)
        if 'created_at' in data:
            validated['created_at'] = validate_datetime(data['created_at'], 'created_at')
        if 'micro_exercise' in data:
            validated['micro_exercise'] = validate_optional_string(data['micro_exercise'], 'micro_exercise', 500)
        
        return validated