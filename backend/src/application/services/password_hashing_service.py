"""Password hashing service using bcrypt."""

from passlib.context import CryptContext


class PasswordHashingService:
    """Service for password hashing and verification."""
    
    def __init__(self, rounds: int = 12):
        """Initialize password hashing service.
        
        Args:
            rounds: Number of bcrypt rounds
        """
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.rounds = rounds
    
    def hash_password(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        return self.pwd_context.verify(plain_password, hashed_password)