"""OpenAI LLM client implementation."""

import asyncio
import time
import random
from typing import List, Dict, Any, Optional, AsyncGenerator
import openai
from openai import AsyncOpenAI
import tiktoken

from .llm_service_interface import (
    LLMServiceInterface,
    LLMProvider,
    LLMModel,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    LLMServiceError,
    LLMRateLimitError,
    LLMQuotaExceededError,
    LLMInvalidRequestError,
    LLMServiceUnavailableError
)
import logging

logger = logging.getLogger(__name__)


class OpenAILLMClient(LLMServiceInterface):
    """OpenAI LLM service implementation."""
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_retry_delay: float = 60.0
    ):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            base_url: Optional base URL for API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Initial retry delay in seconds
            max_retry_delay: Maximum retry delay in seconds
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_retry_delay = max_retry_delay
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
        
        # Token encoders cache
        self._encoders: Dict[str, tiktoken.Encoding] = {}
    
    @property
    def provider(self) -> LLMProvider:
        """Get the provider type."""
        return LLMProvider.OPENAI
    
    @property
    def supported_models(self) -> List[LLMModel]:
        """Get list of supported models."""
        return [
            LLMModel.GPT_3_5_TURBO,
            LLMModel.GPT_4,
            LLMModel.GPT_4_TURBO
        ]
    
    def _get_encoder(self, model: LLMModel) -> tiktoken.Encoding:
        """Get token encoder for model.
        
        Args:
            model: Model to get encoder for
            
        Returns:
            Token encoder
        """
        model_name = model.value
        
        if model_name not in self._encoders:
            try:
                # Try to get encoding for specific model
                self._encoders[model_name] = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # Fallback to cl100k_base encoding for newer models
                self._encoders[model_name] = tiktoken.get_encoding("cl100k_base")
        
        return self._encoders[model_name]
    
    def _map_openai_error(self, error: Exception) -> LLMServiceError:
        """Map OpenAI error to LLM service error.
        
        Args:
            error: OpenAI error
            
        Returns:
            Mapped LLM service error
        """
        if isinstance(error, openai.RateLimitError):
            retry_after = getattr(error, 'retry_after', None)
            return LLMRateLimitError(
                f"Rate limit exceeded: {str(error)}",
                self.provider,
                error_code="rate_limit_exceeded",
                retry_after=retry_after,
                original_error=error
            )
        
        elif isinstance(error, openai.APIError):
            if error.status_code == 429:
                return LLMRateLimitError(
                    f"Rate limit exceeded: {str(error)}",
                    self.provider,
                    error_code="rate_limit_exceeded",
                    original_error=error
                )
            elif error.status_code == 402:
                return LLMQuotaExceededError(
                    f"Quota exceeded: {str(error)}",
                    self.provider,
                    error_code="quota_exceeded",
                    original_error=error
                )
            elif error.status_code in (400, 422):
                return LLMInvalidRequestError(
                    f"Invalid request: {str(error)}",
                    self.provider,
                    error_code="invalid_request",
                    original_error=error
                )
            elif error.status_code >= 500:
                return LLMServiceUnavailableError(
                    f"Service unavailable: {str(error)}",
                    self.provider,
                    error_code="service_unavailable",
                    original_error=error
                )
        
        elif isinstance(error, openai.APIConnectionError):
            return LLMServiceUnavailableError(
                f"Connection error: {str(error)}",
                self.provider,
                error_code="connection_error",
                original_error=error
            )
        
        elif isinstance(error, openai.APITimeoutError):
            return LLMServiceUnavailableError(
                f"Request timeout: {str(error)}",
                self.provider,
                error_code="timeout",
                original_error=error
            )
        
        # Default mapping
        return LLMServiceError(
            f"OpenAI API error: {str(error)}",
            self.provider,
            error_code="unknown_error",
            original_error=error
        )
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            LLMServiceError: If all retries fail
        """
        last_error = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                last_error = self._map_openai_error(e)
                
                # Don't retry on invalid requests
                if isinstance(last_error, LLMInvalidRequestError):
                    raise last_error
                
                # Don't retry on final attempt
                if attempt == self.max_retries:
                    break
                
                # Calculate delay with jitter
                jitter = random.uniform(0.1, 0.3) * delay
                actual_delay = delay + jitter
                
                logger.warning(
                    f"OpenAI API request failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                    f"retrying in {actual_delay:.2f}s: {str(e)}"
                )
                
                await asyncio.sleep(actual_delay)
                
                # Exponential backoff
                delay = min(delay * 2, self.max_retry_delay)
        
        # All retries failed
        raise last_error
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from OpenAI.
        
        Args:
            request: LLM request
            
        Returns:
            LLM response
            
        Raises:
            LLMServiceError: If the request fails
        """
        start_time = time.time()
        
        # Validate request
        self.validate_request(request)
        
        # Prepare OpenAI request
        openai_request = {
            "model": request.model.value,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False
        }
        
        # Add optional parameters
        if request.top_p is not None:
            openai_request["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            openai_request["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            openai_request["presence_penalty"] = request.presence_penalty
        if request.stop:
            openai_request["stop"] = request.stop
        if request.user_id:
            openai_request["user"] = request.user_id
        
        # Add prompt version header if specified
        extra_headers = {}
        if request.prompt_version:
            extra_headers["X-Prompt-Version"] = request.prompt_version
        
        async def _make_request():
            return await self.client.chat.completions.create(
                **openai_request,
                extra_headers=extra_headers
            )
        
        # Execute with retry
        response = await self._retry_with_backoff(_make_request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Extract response data
        choice = response.choices[0]
        content = choice.message.content or ""
        
        # Create LLM response
        llm_response = LLMResponse(
            content=content,
            model=response.model,
            provider=self.provider,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            finish_reason=choice.finish_reason,
            response_time_ms=response_time_ms,
            prompt_version=request.prompt_version,
            metadata={
                "request_id": getattr(response, 'id', None),
                "model_version": response.model,
                "system_fingerprint": getattr(response, 'system_fingerprint', None)
            }
        )
        
        logger.info(
            f"OpenAI response generated",
            extra={
                "model": request.model.value,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "response_time_ms": response_time_ms,
                "finish_reason": choice.finish_reason
            }
        )
        
        return llm_response
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMStreamChunk, None]:
        """Generate a streaming response from OpenAI.
        
        Args:
            request: LLM request
            
        Yields:
            LLMStreamChunk: Streaming response chunks
            
        Raises:
            LLMServiceError: If the request fails
        """
        # Validate request
        self.validate_request(request)
        
        # Prepare OpenAI request
        openai_request = {
            "model": request.model.value,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": True
        }
        
        # Add optional parameters
        if request.top_p is not None:
            openai_request["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            openai_request["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            openai_request["presence_penalty"] = request.presence_penalty
        if request.stop:
            openai_request["stop"] = request.stop
        if request.user_id:
            openai_request["user"] = request.user_id
        
        # Add prompt version header if specified
        extra_headers = {}
        if request.prompt_version:
            extra_headers["X-Prompt-Version"] = request.prompt_version
        
        async def _make_stream_request():
            return await self.client.chat.completions.create(
                **openai_request,
                extra_headers=extra_headers
            )
        
        try:
            # Execute with retry
            stream = await self._retry_with_backoff(_make_stream_request)
            
            async for chunk in stream:
                if chunk.choices:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    if delta.content:
                        yield LLMStreamChunk(
                            content=delta.content,
                            is_complete=choice.finish_reason is not None,
                            model=chunk.model,
                            provider=self.provider,
                            metadata={
                                "finish_reason": choice.finish_reason,
                                "index": choice.index
                            }
                        )
                    
                    # Final chunk
                    if choice.finish_reason:
                        yield LLMStreamChunk(
                            content="",
                            is_complete=True,
                            model=chunk.model,
                            provider=self.provider,
                            metadata={
                                "finish_reason": choice.finish_reason,
                                "index": choice.index
                            }
                        )
                        break
        
        except Exception as e:
            raise self._map_openai_error(e)
    
    async def is_available(self) -> bool:
        """Check if OpenAI service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            # Make a simple request to check availability
            await self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI service unavailable: {str(e)}")
            return False
    
    async def get_model_info(self, model: LLMModel) -> Dict[str, Any]:
        """Get information about a specific model.
        
        Args:
            model: Model to get information for
            
        Returns:
            Dictionary with model information
        """
        try:
            model_info = await self.client.models.retrieve(model.value)
            return {
                "id": model_info.id,
                "object": model_info.object,
                "created": model_info.created,
                "owned_by": model_info.owned_by,
                "provider": self.provider.value
            }
        except Exception as e:
            logger.warning(f"Failed to get model info for {model.value}: {str(e)}")
            return {
                "id": model.value,
                "provider": self.provider.value,
                "error": str(e)
            }
    
    def estimate_tokens(self, text: str, model: LLMModel) -> int:
        """Estimate token count for text.
        
        Args:
            text: Text to estimate tokens for
            model: Model to use for estimation
            
        Returns:
            Estimated token count
        """
        try:
            encoder = self._get_encoder(model)
            return len(encoder.encode(text))
        except Exception as e:
            logger.warning(f"Failed to estimate tokens: {str(e)}")
            # Fallback estimation (rough approximation)
            return len(text.split()) * 1.3
    
    def validate_request(self, request: LLMRequest) -> None:
        """Validate LLM request.
        
        Args:
            request: Request to validate
            
        Raises:
            LLMInvalidRequestError: If request is invalid
        """
        # Check model support
        if request.model not in self.supported_models:
            raise LLMInvalidRequestError(
                f"Model {request.model.value} not supported by OpenAI provider",
                self.provider,
                error_code="unsupported_model"
            )
        
        # Check messages
        if not request.messages:
            raise LLMInvalidRequestError(
                "Messages cannot be empty",
                self.provider,
                error_code="empty_messages"
            )
        
        # Check message format
        for i, message in enumerate(request.messages):
            if not isinstance(message, dict):
                raise LLMInvalidRequestError(
                    f"Message {i} must be a dictionary",
                    self.provider,
                    error_code="invalid_message_format"
                )
            
            if "role" not in message or "content" not in message:
                raise LLMInvalidRequestError(
                    f"Message {i} must have 'role' and 'content' fields",
                    self.provider,
                    error_code="missing_message_fields"
                )
            
            if message["role"] not in ["system", "user", "assistant"]:
                raise LLMInvalidRequestError(
                    f"Message {i} has invalid role: {message['role']}",
                    self.provider,
                    error_code="invalid_message_role"
                )
        
        # Check parameters
        if request.max_tokens is not None and request.max_tokens <= 0:
            raise LLMInvalidRequestError(
                "max_tokens must be positive",
                self.provider,
                error_code="invalid_max_tokens"
            )
        
        if request.temperature is not None and not (0 <= request.temperature <= 2):
            raise LLMInvalidRequestError(
                "temperature must be between 0 and 2",
                self.provider,
                error_code="invalid_temperature"
            )
        
        if request.top_p is not None and not (0 <= request.top_p <= 1):
            raise LLMInvalidRequestError(
                "top_p must be between 0 and 1",
                self.provider,
                error_code="invalid_top_p"
            )