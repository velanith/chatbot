"""OpenRouter LLM client implementation."""

import asyncio
import time
import random
from typing import List, Dict, Any, Optional, AsyncGenerator
import aiohttp
import json

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


class OpenRouterLLMClient(LLMServiceInterface):
    """OpenRouter LLM service implementation."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        app_name: str = "Polyglot",
        app_url: str = "https://github.com/your-repo"
    ):
        """Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            base_url: OpenRouter API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Initial retry delay in seconds
            max_retry_delay: Maximum retry delay in seconds
            app_name: Application name for OpenRouter
            app_url: Application URL for OpenRouter
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_retry_delay = max_retry_delay
        self.app_name = app_name
        self.app_url = app_url
        
        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_setup = False
    
    async def _setup_session(self):
        """Setup aiohttp session with proper headers."""
        if self._session_setup and self._session and not self._session.closed:
            return
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_url,
            "X-Title": self.app_name,
            "User-Agent": f"{self.app_name}/1.0"
        }
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout
        )
        self._session_setup = True
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    @property
    def provider(self) -> LLMProvider:
        """Get the provider type."""
        return LLMProvider.OPENROUTER
    
    @property
    def supported_models(self) -> List[LLMModel]:
        """Get list of supported models."""
        return [
            # OpenAI models via OpenRouter
            LLMModel.GPT_3_5_TURBO,
            LLMModel.GPT_4,
            LLMModel.GPT_4_TURBO,
            # OpenRouter specific models
            LLMModel.CLAUDE_3_OPUS,
            LLMModel.CLAUDE_3_SONNET,
            LLMModel.LLAMA_2_70B,
            LLMModel.MIXTRAL_8X7B
        ]
    
    def _map_http_error(self, status_code: int, response_data: Dict[str, Any]) -> LLMServiceError:
        """Map HTTP error to LLM service error.
        
        Args:
            status_code: HTTP status code
            response_data: Response data
            
        Returns:
            Mapped LLM service error
        """
        error_message = response_data.get("error", {}).get("message", "Unknown error")
        error_code = response_data.get("error", {}).get("code", "unknown")
        
        if status_code == 429:
            return LLMRateLimitError(
                f"Rate limit exceeded: {error_message}",
                self.provider,
                error_code="rate_limit_exceeded"
            )
        elif status_code == 402:
            return LLMQuotaExceededError(
                f"Quota exceeded: {error_message}",
                self.provider,
                error_code="quota_exceeded"
            )
        elif status_code in (400, 422):
            return LLMInvalidRequestError(
                f"Invalid request: {error_message}",
                self.provider,
                error_code="invalid_request"
            )
        elif status_code >= 500:
            return LLMServiceUnavailableError(
                f"Service unavailable: {error_message}",
                self.provider,
                error_code="service_unavailable"
            )
        else:
            return LLMServiceError(
                f"OpenRouter API error: {error_message}",
                self.provider,
                error_code=error_code
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
                if isinstance(e, LLMServiceError):
                    last_error = e
                else:
                    last_error = LLMServiceError(
                        f"Unexpected error: {str(e)}",
                        self.provider,
                        original_error=e
                    )
                
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
                    f"OpenRouter API request failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                    f"retrying in {actual_delay:.2f}s: {str(e)}"
                )
                
                await asyncio.sleep(actual_delay)
                
                # Exponential backoff
                delay = min(delay * 2, self.max_retry_delay)
        
        # All retries failed
        raise last_error
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from OpenRouter.
        
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
        
        # Ensure session is setup
        await self._setup_session()
        
        # Prepare OpenRouter request
        openrouter_request = {
            "model": request.model.value,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False
        }
        
        # Add optional parameters
        if request.top_p is not None:
            openrouter_request["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            openrouter_request["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            openrouter_request["presence_penalty"] = request.presence_penalty
        if request.stop:
            openrouter_request["stop"] = request.stop
        
        # Add OpenRouter specific parameters
        if request.user_id:
            openrouter_request["user"] = request.user_id
        
        # Add prompt version header if specified
        extra_headers = {}
        if request.prompt_version:
            extra_headers["X-Prompt-Version"] = request.prompt_version
        
        async def _make_request():
            async with self._session.post(
                f"{self.base_url}/chat/completions",
                json=openrouter_request,
                headers=extra_headers
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    raise self._map_http_error(response.status, response_data)
                
                return response_data
        
        # Execute with retry
        response_data = await self._retry_with_backoff(_make_request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Extract response data
        choice = response_data["choices"][0]
        content = choice["message"]["content"] or ""
        
        # Create LLM response
        llm_response = LLMResponse(
            content=content,
            model=response_data["model"],
            provider=self.provider,
            usage={
                "prompt_tokens": response_data.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response_data.get("usage", {}).get("completion_tokens", 0),
                "total_tokens": response_data.get("usage", {}).get("total_tokens", 0)
            },
            finish_reason=choice.get("finish_reason", "stop"),
            response_time_ms=response_time_ms,
            prompt_version=request.prompt_version,
            metadata={
                "request_id": response_data.get("id"),
                "model_version": response_data["model"],
                "provider_metadata": response_data.get("provider", {})
            }
        )
        
        logger.info(
            f"OpenRouter response generated",
            extra={
                "model": request.model.value,
                "prompt_tokens": llm_response.usage["prompt_tokens"],
                "completion_tokens": llm_response.usage["completion_tokens"],
                "response_time_ms": response_time_ms,
                "finish_reason": choice.get("finish_reason")
            }
        )
        
        return llm_response
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[LLMStreamChunk, None]:
        """Generate a streaming response from OpenRouter.
        
        Args:
            request: LLM request
            
        Yields:
            LLMStreamChunk: Streaming response chunks
            
        Raises:
            LLMServiceError: If the request fails
        """
        # Validate request
        self.validate_request(request)
        
        # Ensure session is setup
        await self._setup_session()
        
        # Prepare OpenRouter request
        openrouter_request = {
            "model": request.model.value,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": True
        }
        
        # Add optional parameters
        if request.top_p is not None:
            openrouter_request["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            openrouter_request["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            openrouter_request["presence_penalty"] = request.presence_penalty
        if request.stop:
            openrouter_request["stop"] = request.stop
        if request.user_id:
            openrouter_request["user"] = request.user_id
        
        # Add prompt version header if specified
        extra_headers = {}
        if request.prompt_version:
            extra_headers["X-Prompt-Version"] = request.prompt_version
        
        async def _make_stream_request():
            return self._session.post(
                f"{self.base_url}/chat/completions",
                json=openrouter_request,
                headers=extra_headers
            )
        
        try:
            # Execute with retry
            response = await self._retry_with_backoff(_make_stream_request)
            
            async with response as resp:
                if resp.status != 200:
                    response_data = await resp.json()
                    raise self._map_http_error(resp.status, response_data)
                
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line or not line.startswith('data: '):
                        continue
                    
                    if line == 'data: [DONE]':
                        break
                    
                    try:
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        
                        if data.get("choices"):
                            choice = data["choices"][0]
                            delta = choice.get("delta", {})
                            
                            if delta.get("content"):
                                yield LLMStreamChunk(
                                    content=delta["content"],
                                    is_complete=choice.get("finish_reason") is not None,
                                    model=data.get("model", request.model.value),
                                    provider=self.provider,
                                    metadata={
                                        "finish_reason": choice.get("finish_reason"),
                                        "index": choice.get("index", 0)
                                    }
                                )
                            
                            # Final chunk
                            if choice.get("finish_reason"):
                                yield LLMStreamChunk(
                                    content="",
                                    is_complete=True,
                                    model=data.get("model", request.model.value),
                                    provider=self.provider,
                                    metadata={
                                        "finish_reason": choice.get("finish_reason"),
                                        "index": choice.get("index", 0)
                                    }
                                )
                                break
                    
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
        
        except Exception as e:
            if isinstance(e, LLMServiceError):
                raise
            raise LLMServiceError(
                f"OpenRouter streaming error: {str(e)}",
                self.provider,
                original_error=e
            )
    
    async def is_available(self) -> bool:
        """Check if OpenRouter service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            # Ensure session is setup
            await self._setup_session()
            
            # Make a simple request to check availability
            async with self._session.get(f"{self.base_url}/models") as response:
                return response.status == 200
        
        except Exception as e:
            logger.warning(f"OpenRouter service unavailable: {str(e)}")
            return False
    
    async def get_model_info(self, model: LLMModel) -> Dict[str, Any]:
        """Get information about a specific model.
        
        Args:
            model: Model to get information for
            
        Returns:
            Dictionary with model information
        """
        try:
            # Ensure session is setup
            await self._setup_session()
            
            async with self._session.get(f"{self.base_url}/models/{model.value}") as response:
                if response.status == 200:
                    model_info = await response.json()
                    return {
                        "id": model_info.get("id", model.value),
                        "name": model_info.get("name", model.value),
                        "description": model_info.get("description", ""),
                        "context_length": model_info.get("context_length", 0),
                        "pricing": model_info.get("pricing", {}),
                        "provider": self.provider.value
                    }
                else:
                    logger.warning(f"Failed to get model info for {model.value}: HTTP {response.status}")
                    return {
                        "id": model.value,
                        "provider": self.provider.value,
                        "error": f"HTTP {response.status}"
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
        # Simple estimation based on word count
        # This is a rough approximation since we don't have access to model-specific tokenizers
        words = len(text.split())
        
        # Different models have different token-to-word ratios
        if "claude" in model.value.lower():
            # Claude models tend to have slightly different tokenization
            return int(words * 1.2)
        elif "llama" in model.value.lower():
            # Llama models
            return int(words * 1.3)
        else:
            # Default estimation (similar to GPT models)
            return int(words * 1.3)
    
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
                f"Model {request.model.value} not supported by OpenRouter provider",
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