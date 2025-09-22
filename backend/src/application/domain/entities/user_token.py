"""User token domain entity for JWT authentication."""

import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Union

from ..exceptions import ValidationError


@dataclass
class UserToken:
    """User token entity representing a JWT authentication token."""
    
    user_id: Union[str, uuid.UUID]
    username: str
    token: str
    expires_at: datetime
    created_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validate token data after initialization."""
        self._validate_user_id()
        self._validate_username()
        self._validate_token()
        self._validate_expiration()
        
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def _validate_user_id(self) -> None:
        """Validate user ID."""
        if not self.user_id:
            raise ValidationError("User ID cannot be empty")
        
        # Convert string to UUID if needed
        if isinstance(self.user_id, str):
            try:
                self.user_id = uuid.UUID(self.user_id)
            except ValueError:
                raise ValidationError("User ID must be a valid UUID")
        elif not isinstance(self.user_id, uuid.UUID):
            raise ValidationError("User ID must be a UUID")
    
    def _validate_username(self) -> None:
        """Validate username."""
        if not self.username or not isinstance(self.username, str):
            raise ValidationError("Username must be a non-empty string")
        
        if len(self.username) < 3 or len(self.username) > 50:
            raise ValidationError("Username must be between 3 and 50 characters")
    
    def _validate_token(self) -> None:
        """Validate JWT token format."""
        if not self.token or not isinstance(self.token, str):
            raise ValidationError("Token must be a non-empty string")
        
        # Basic JWT format validation (3 parts separated by dots)
        parts = self.token.split('.')
        if len(parts) != 3:
            raise ValidationError("Invalid JWT token format")
        
        # Check that each part is not empty
        if not all(part for part in parts):
            raise ValidationError("Invalid JWT token format")
    
    def _validate_expiration(self) -> None:
        """Validate token expiration."""
        if not isinstance(self.expires_at, datetime):
            raise ValidationError("Expiration must be a datetime object")
        
        if self.expires_at <= datetime.utcnow():
            raise ValidationError("Token expiration must be in the future")
    
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.utcnow() >= self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the token is still valid (not expired)."""
        return not self.is_expired()
    
    def time_until_expiry(self) -> timedelta:
        """Get the time remaining until token expiry."""
        return self.expires_at - datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert token entity to dictionary representation."""
        return {
            'user_id': str(self.user_id),
            'username': self.username,
            'token': self.token,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserToken':
        """Create token entity from dictionary representation."""
        expires_at = datetime.fromisoformat(data['expires_at'])
        created_at = None
        
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        user_id = uuid.UUID(data['user_id']) if isinstance(data['user_id'], str) else data['user_id']
        
        return cls(
            user_id=user_id,
            username=data['username'],
            token=data['token'],
            expires_at=expires_at,
            created_at=created_at,
        )
    
    @classmethod
    def create_for_user(
        cls, 
        user_id: Union[str, uuid.UUID], 
        username: str, 
        token: str, 
        expiration_hours: int = 24
    ) -> 'UserToken':
        """Create a new token for a user with specified expiration."""
        expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        return cls(
            user_id=user_id,
            username=username,
            token=token,
            expires_at=expires_at,
        )
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on token value."""
        if not isinstance(other, UserToken):
            return False
        return self.token == other.token
    
    def __hash__(self) -> int:
        """Hash based on token value."""
        return hash(self.token)
    
    def __str__(self) -> str:
        """String representation of the token (masked for security)."""
        masked_token = self.token[:10] + "..." + self.token[-10:] if len(self.token) > 20 else "***"
        return f"UserToken(user_id={self.user_id}, token={masked_token})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the token."""
        return (
            f"UserToken(user_id={self.user_id}, username='{self.username}', "
            f"expires_at={self.expires_at}, valid={self.is_valid()})"
        )