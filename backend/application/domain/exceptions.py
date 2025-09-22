"""Domain exceptions for the user registration system."""


class DomainException(Exception):
    """Base exception for domain-related errors."""
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ValidationError(DomainException):
    """Exception raised when domain validation fails."""
    pass


class UserAlreadyExistsException(DomainException):
    """Exception raised when trying to create a user that already exists."""
    pass


class InvalidCredentialsException(DomainException):
    """Exception raised when authentication credentials are invalid."""
    pass


class UserNotFoundException(DomainException):
    """Exception raised when a requested user cannot be found."""
    pass


class RepositoryException(DomainException):
    """Exception raised when repository operations fail."""
    pass


class DatabaseException(DomainException):
    """Exception raised when database operations fail."""
    pass


class InvalidTokenException(DomainException):
    """Exception raised when JWT token is invalid."""
    pass


class TokenExpiredException(DomainException):
    """Exception raised when JWT token has expired."""
    pass