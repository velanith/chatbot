"""JWT token service for authentication."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import JWTError, jwt

from src.domain.exceptions.base_exceptions import AuthenticationError


class JWTService:
    """Service for JWT token creation and validation."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expiration_hours: int = 24
    ):
        """Initialize JWT service.
        
        Args:
            secret_key: Secret key for token signing
            algorithm: JWT algorithm to use
            expiration_hours: Token expiration time in hours
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def create_token(self, user_id: str, username: str, **extra_claims) -> str:
        """Create a JWT token for a user.
        
        Args:
            user_id: User ID to include in token
            username: Username to include in token
            **extra_claims: Additional claims to include
            
        Returns:
            JWT token string
        """
        # Calculate expiration time
        expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)
        
        # Create token payload
        payload = {
            "sub": username,
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            **extra_claims
        }
        
        # Create and return token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate a JWT token and return payload.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Token payload as dictionary
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check if token has required fields
            if "sub" not in payload or "user_id" not in payload:
                raise AuthenticationError("Invalid token payload")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTClaimsError:
            raise AuthenticationError("Invalid token claims")
        except JWTError:
            raise AuthenticationError("Invalid token")
    
    def refresh_token(self, token: str) -> str:
        """Refresh a JWT token.
        
        Args:
            token: Current JWT token
            
        Returns:
            New JWT token
            
        Raises:
            AuthenticationError: If token is invalid
        """
        # Validate current token
        payload = self.validate_token(token)
        
        # Create new token with same claims (except exp and iat)
        user_id = payload["user_id"]
        username = payload["sub"]
        
        # Remove time-based claims
        extra_claims = {
            k: v for k, v in payload.items()
            if k not in ["sub", "user_id", "exp", "iat"]
        }
        
        return self.create_token(user_id, username, **extra_claims)
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification (for debugging).
        
        Args:
            token: JWT token to decode
            
        Returns:
            Token payload or None if invalid
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
        except Exception:
            return None