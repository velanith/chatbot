"""User registration use case implementing the business workflow."""

import uuid
from typing import Dict, Any
from dataclasses import dataclass

from src.domain.entities.user import User
from src.domain.entities.password import Password
from src.domain.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.exceptions import (
    ValidationError,
    ConflictError
)
from src.application.services.password_hashing_service import PasswordHashingService


@dataclass
class UserRegistrationRequest:
    """Request data for user registration."""
    username: str
    email: str
    password: str
    native_language: str = 'TR'
    target_language: str = 'EN'
    proficiency_level: str = 'A2'


@dataclass
class UserRegistrationResponse:
    """Response data for user registration."""
    user_id: uuid.UUID
    username: str
    email: str
    created_at: str
    message: str
    user_profile: Dict[str, Any]  # Add user profile for API response


class UserRegistrationUseCase:
    """Use case for registering new users.
    
    This use case handles the complete user registration workflow:
    1. Validate input data
    2. Check if user already exists
    3. Validate password requirements
    4. Hash the password
    5. Create and save the user
    6. Return registration response
    """
    
    def __init__(
        self,
        user_repository: UserRepositoryInterface,
        password_service: PasswordHashingService
    ):
        """Initialize the use case with required dependencies.
        
        Args:
            user_repository: Repository for user data operations
            password_service: Service for password hashing
        """
        self._user_repository = user_repository
        self._password_service = password_service
    
    async def execute(self, request: UserRegistrationRequest) -> UserRegistrationResponse:
        """Execute the user registration workflow.
        
        Args:
            request: User registration request data
            
        Returns:
            UserRegistrationResponse with created user information
            
        Raises:
            ValidationError: If input data is invalid
            UserAlreadyExistsException: If user already exists
        """
        # Step 1: Validate input data
        self._validate_request(request)
        
        # Step 2: Check if user already exists
        await self._check_user_existence(request.username, request.email)
        
        # Step 3: Validate password requirements using domain entity
        password_entity = Password(request.password)
        
        # Step 4: Hash the password
        password_hash = self._password_service.hash_password(request.password)
        
        # Step 5: Create user entity
        user = User(
            id=None,  # Will be assigned by repository
            username=request.username,
            email=request.email,
            password_hash=password_hash,
            native_language=request.native_language,
            target_language=request.target_language,
            proficiency_level=request.proficiency_level
        )
        
        # Step 6: Save user to repository
        created_user = await self._user_repository.create(user)
        
        # Step 7: Return success response
        user_profile = {
            "id": str(created_user.id),
            "username": created_user.username,
            "email": created_user.email,
            "is_active": created_user.is_active,
            "is_verified": False,  # New users are not verified by default
            "native_language": created_user.native_language,
            "target_language": created_user.target_language,
            "proficiency_level": created_user.proficiency_level,
            "created_at": created_user.created_at.isoformat(),
            "updated_at": created_user.updated_at.isoformat() if created_user.updated_at else None
        }
        
        return UserRegistrationResponse(
            user_id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            created_at=created_user.created_at.isoformat(),
            message="User registered successfully",
            user_profile=user_profile
        )
    
    def _validate_request(self, request: UserRegistrationRequest) -> None:
        """Validate the registration request data.
        
        Args:
            request: Registration request to validate
            
        Raises:
            ValidationError: If request data is invalid
        """
        if not request:
            raise ValidationError("Registration request cannot be empty")
        
        if not isinstance(request, UserRegistrationRequest):
            raise ValidationError("Invalid request type")
        
        # Validate username
        if not request.username or not isinstance(request.username, str):
            raise ValidationError("Username must be a non-empty string")
        
        if len(request.username.strip()) == 0:
            raise ValidationError("Username cannot be empty or whitespace only")
        
        # Validate email
        if not request.email or not isinstance(request.email, str):
            raise ValidationError("Email must be a non-empty string")
        
        if len(request.email.strip()) == 0:
            raise ValidationError("Email cannot be empty or whitespace only")
        
        # Validate password
        if not request.password or not isinstance(request.password, str):
            raise ValidationError("Password must be a non-empty string")
        
        if len(request.password.strip()) == 0:
            raise ValidationError("Password cannot be empty or whitespace only")
        
        # Validate language preferences
        if not request.native_language or not isinstance(request.native_language, str):
            raise ValidationError("Native language must be a non-empty string")
        
        if not request.target_language or not isinstance(request.target_language, str):
            raise ValidationError("Target language must be a non-empty string")
        
        if not request.proficiency_level or not isinstance(request.proficiency_level, str):
            raise ValidationError("Proficiency level must be a non-empty string")
    
    async def _check_user_existence(self, username: str, email: str) -> None:
        """Check if user already exists with given username or email.
        
        Args:
            username: Username to check
            email: Email to check
            
        Raises:
            UserAlreadyExistsException: If user already exists
        """
        # Check username existence
        if await self._user_repository.exists_by_username(username):
            raise ConflictError(f"Username '{username}' is already taken")
        
        # Check email existence
        if await self._user_repository.exists_by_email(email):
            raise ConflictError(f"Email '{email}' is already registered")
    
    def to_dict(self, response: UserRegistrationResponse) -> Dict[str, Any]:
        """Convert response to dictionary for API serialization.
        
        Args:
            response: Registration response to convert
            
        Returns:
            Dictionary representation of the response
        """
        return {
            "user_id": str(response.user_id),
            "username": response.username,
            "email": response.email,
            "created_at": response.created_at,
            "message": response.message
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> UserRegistrationRequest:
        """Create request from dictionary data.
        
        Args:
            data: Dictionary containing request data
            
        Returns:
            UserRegistrationRequest instance
            
        Raises:
            ValidationError: If data is invalid
        """
        if not data or not isinstance(data, dict):
            raise ValidationError("Request data must be a non-empty dictionary")
        
        required_fields = ['username', 'email', 'password']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return UserRegistrationRequest(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            native_language=data.get('native_language', 'TR'),
            target_language=data.get('target_language', 'EN'),
            proficiency_level=data.get('proficiency_level', 'A2')
        )
    
    def __str__(self) -> str:
        """String representation of the use case."""
        return "UserRegistrationUseCase"
    
    def __repr__(self) -> str:
        """Detailed string representation of the use case."""
        return f"UserRegistrationUseCase(repository={type(self._user_repository).__name__}, password_service={type(self._password_service).__name__})"