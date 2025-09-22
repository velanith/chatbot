"""LLM Service Interface for provider abstraction."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from src.domain.entities.message import Message


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


class LLMModel(str, Enum):
    """Supported LLM models."""
    # OpenAI Models
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    
    # OpenRouter Models (via OpenAI API)
    CLAUDE_3_OPUS = "anthropic/claude-3-opus"
    CLAUDE_3_SONNET = "anthropic/claude-3-sonnet"
    LLAMA_2_70B = "meta-llama/llama-2-70b-chat"
    MIXTRAL_8X7B = "mistralai/mixtral-8x7b-instruct"
    
    # Anthropic Models
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Cohere Models
    COMMAND_R = "command-r"
    COMMAND_R_PLUS = "command-r-plus"


@dataclass
class LLMRequest:
    """Request data for LLM service."""
    messages: List[Dict[str, str]]
    model: LLMModel
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None
    stream: bool = False
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    prompt_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Response data from LLM service."""
    content: str
    model: str
    provider: LLMProvider
    usage: Dict[str, int]
    finish_reason: str
    response_time_ms: float
    prompt_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMStreamChunk:
    """Streaming response chunk from LLM service."""
    content: str
    is_complete: bool
    model: str
    provider: LLMProvider
    metadata: Optional[Dict[str, Any]] = None


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    
    def __init__(
        self, 
        message: str, 
        provider: LLMProvider,
        error_code: Optional[str] = None,
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.retry_after = retry_after
        self.original_error = original_error


class LLMRateLimitError(LLMServiceError):
    """Rate limit exceeded error."""
    pass


class LLMQuotaExceededError(LLMServiceError):
    """Quota exceeded error."""
    pass


class LLMInvalidRequestError(LLMServiceError):
    """Invalid request error."""
    pass


class LLMServiceUnavailableError(LLMServiceError):
    """Service unavailable error."""
    pass


class LLMServiceInterface(ABC):
    """Abstract interface for LLM service providers."""
    
    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Get the provider type."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[LLMModel]:
        """Get list of supported models."""
        pass
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            request: LLM request with messages and parameters
            
        Returns:
            LLM response with generated content
            
        Raises:
            LLMServiceError: If the request fails
        """
        pass
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMStreamChunk, None]:
        """Generate a streaming response from the LLM.
        
        Args:
            request: LLM request with messages and parameters
            
        Yields:
            LLMStreamChunk: Streaming response chunks
            
        Raises:
            LLMServiceError: If the request fails
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_model_info(self, model: LLMModel) -> Dict[str, Any]:
        """Get information about a specific model.
        
        Args:
            model: Model to get information for
            
        Returns:
            Dictionary with model information
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str, model: LLMModel) -> int:
        """Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for
            model: Model to use for estimation
            
        Returns:
            Estimated token count
        """
        pass
    
    @abstractmethod
    def validate_request(self, request: LLMRequest) -> None:
        """Validate LLM request.
        
        Args:
            request: Request to validate
            
        Raises:
            LLMInvalidRequestError: If request is invalid
        """
        pass


class LLMServiceFactory:
    """Factory for creating LLM service instances."""
    
    _services: Dict[LLMProvider, type] = {}
    
    @classmethod
    def register_service(cls, provider: LLMProvider, service_class: type) -> None:
        """Register a service implementation.
        
        Args:
            provider: Provider type
            service_class: Service implementation class
        """
        cls._services[provider] = service_class
    
    @classmethod
    def create_service(
        cls, 
        provider: LLMProvider, 
        **kwargs
    ) -> LLMServiceInterface:
        """Create a service instance.
        
        Args:
            provider: Provider type
            **kwargs: Service-specific configuration
            
        Returns:
            LLM service instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls._services:
            raise ValueError(f"Unsupported provider: {provider}")
        
        service_class = cls._services[provider]
        return service_class(**kwargs)
    
    @classmethod
    def get_supported_providers(cls) -> List[LLMProvider]:
        """Get list of supported providers.
        
        Returns:
            List of supported providers
        """
        return list(cls._services.keys())


class LLMServiceManager:
    """Manager for multiple LLM services with failover support."""
    
    def __init__(self, services: List[LLMServiceInterface]):
        """Initialize with list of services.
        
        Args:
            services: List of LLM services in priority order
        """
        self.services = services
        self.primary_service = services[0] if services else None
        self.fallback_services = services[1:] if len(services) > 1 else []
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response with automatic failover.
        
        Args:
            request: LLM request
            
        Returns:
            LLM response from first available service
            
        Raises:
            LLMServiceError: If all services fail
        """
        last_error = None
        
        for service in self.services:
            try:
                # Check if service is available
                if not await service.is_available():
                    continue
                
                # Validate request for this service
                service.validate_request(request)
                
                # Generate response
                return await service.generate_response(request)
                
            except (LLMRateLimitError, LLMQuotaExceededError, LLMServiceUnavailableError) as e:
                # These errors should trigger failover
                last_error = e
                continue
                
            except LLMInvalidRequestError:
                # Invalid request shouldn't trigger failover
                raise
                
            except Exception as e:
                # Unexpected errors should trigger failover
                last_error = LLMServiceError(
                    f"Unexpected error from {service.provider}: {str(e)}",
                    service.provider,
                    original_error=e
                )
                continue
        
        # All services failed
        if last_error:
            raise last_error
        else:
            raise LLMServiceError(
                "No available LLM services",
                LLMProvider.OPENAI  # Default provider for error
            )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMStreamChunk, None]:
        """Generate streaming response with automatic failover.
        
        Args:
            request: LLM request
            
        Yields:
            LLMStreamChunk: Streaming response chunks
            
        Raises:
            LLMServiceError: If all services fail
        """
        last_error = None
        
        for service in self.services:
            try:
                # Check if service is available
                if not await service.is_available():
                    continue
                
                # Validate request for this service
                service.validate_request(request)
                
                # Generate streaming response
                async for chunk in service.generate_stream(request):
                    yield chunk
                return
                
            except (LLMRateLimitError, LLMQuotaExceededError, LLMServiceUnavailableError) as e:
                # These errors should trigger failover
                last_error = e
                continue
                
            except LLMInvalidRequestError:
                # Invalid request shouldn't trigger failover
                raise
                
            except Exception as e:
                # Unexpected errors should trigger failover
                last_error = LLMServiceError(
                    f"Unexpected error from {service.provider}: {str(e)}",
                    service.provider,
                    original_error=e
                )
                continue
        
        # All services failed
        if last_error:
            raise last_error
        else:
            raise LLMServiceError(
                "No available LLM services",
                LLMProvider.OPENAI  # Default provider for error
            )
    
    def get_available_models(self) -> List[LLMModel]:
        """Get all available models from all services.
        
        Returns:
            List of available models
        """
        models = set()
        for service in self.services:
            models.update(service.supported_models)
        return list(models)
    
    def get_service_for_model(self, model: LLMModel) -> Optional[LLMServiceInterface]:
        """Get the best service for a specific model.
        
        Args:
            model: Model to find service for
            
        Returns:
            Service that supports the model, or None
        """
        for service in self.services:
            if model in service.supported_models:
                return service
        return None