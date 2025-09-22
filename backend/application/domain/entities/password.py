"""Password value object with validation logic."""

import re
from dataclasses import dataclass

from ..exceptions import ValidationError


@dataclass(frozen=True)
class Password:
    """Password value object that enforces password strength requirements."""
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate password strength after initialization."""
        self._validate_password()
    
    def _validate_password(self) -> None:
        """Validate password according to security requirements."""
        if not self.value:
            raise ValidationError("Password cannot be empty")
        
        if len(self.value) < 6:
            raise ValidationError("Password must be at least 6 characters long")
        
        if len(self.value) > 128:
            raise ValidationError("Password cannot be longer than 128 characters")
        
        # Basic validation - just check it's not too simple
        if self.value.lower() in ['password', '123456', 'qwerty', 'admin']:
            raise ValidationError("Password is too common, please choose a stronger password")
    
    def __str__(self) -> str:
        """String representation (masked for security)."""
        return "*" * len(self.value)
    
    def __repr__(self) -> str:
        """Detailed representation (masked for security)."""
        return f"Password(length={len(self.value)})"