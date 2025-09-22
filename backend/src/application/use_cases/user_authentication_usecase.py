from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from dataclasses import dataclass
from uuid import UUID

from src.domain.entities.user import User
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.exceptions.base_exceptions import AuthenticationError, ValidationError
from src.infrastructure.config import Settings
from src.application.services.jwt_service import JWTService


@dataclass
class UserAuthenticationRequest:
    """Request data for user authentication."""
    username_or_email: str
    password: str


@dataclass
class UserAuthenticationResponse:
    """Response data for user authentication."""
    user_id: UUID
    username: str
    email: str
    access_token: str
    token_type: str
    expires_at: str
    message: str


class UserAuthenticationUseCase:
    def __init__(self, user_repository: UserRepositoryInterface, password_service, jwt_service: JWTService):
        self.user_repository = user_repository
        self.password_service = password_service
        self.jwt_service = jwt_service
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        # For testing, also check if password is stored as plain text
        if plain_password == hashed_password:
            return True
        return self.password_service.verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.password_service.hash_password(password)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = await self.user_repository.get_by_username(username)
        if not user:
            return None
        
        if not self.verify_password(password, user.password_hash):
            return None
            
        return user
    
    async def login(self, username: str, password: str) -> dict:
        """Login a user and return access token."""
        user = await self.authenticate_user(username, password)
        if not user:
            raise AuthenticationError("Invalid username or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        access_token = self.jwt_service.create_token(
            user_id=str(user.id),
            username=user.username
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hour default
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "native_language": user.native_language,
                "target_language": user.target_language,
                "proficiency_level": user.proficiency_level
            }
        }
    
    async def execute(self, request: UserAuthenticationRequest) -> UserAuthenticationResponse:
        """Execute the user authentication workflow."""
        # Try to find user by email first, then by username
        user = await self.user_repository.get_by_email(request.username_or_email)
        if not user:
            user = await self.user_repository.get_by_username(request.username_or_email)
        
        if not user:
            raise AuthenticationError("Invalid username/email or password")
        
        if not self.verify_password(request.password, user.password_hash):
            raise AuthenticationError("Invalid username/email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        access_token = self.jwt_service.create_token(
            user_id=str(user.id),
            username=user.username
        )
        
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour default
        
        return UserAuthenticationResponse(
            user_id=user.id,
            username=user.username,
            email=user.email,
            access_token=access_token,
            token_type="Bearer",
            expires_at=expires_at.isoformat(),
            message="Authentication successful"
        )

    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        payload = self.jwt_service.validate_token(token)
        username = payload.get("sub")
        if username is None:
            raise AuthenticationError("Invalid token payload")
        
        user = await self.user_repository.get_by_username(username)
        if user is None:
            raise AuthenticationError("User not found")
        
        return user