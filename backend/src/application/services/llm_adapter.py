"""Adapter to bridge new LLM service layer with existing OpenAI service interface."""

from typing import List, Dict, Optional
from dataclasses import dataclass
import asyncio

from .llm_service_interface import (
    LLMServiceManager,
    LLMRequest,
    LLMResponse,
    LLMModel,
    LLMServiceError
)
from .llm_service_registry import get_llm_service_manager
from .openai_service import OpenAIResponse, OpenAIServiceError, PromptVersion
from src.domain.entities.conversation_context import ConversationContext
from src.domain.entities.message import MessageRole
from src.infrastructure.config import Settings
import logging

logger = logging.getLogger(__name__)


class LLMAdapter:
    """Adapter to use new LLM service layer with existing interfaces."""
    
    def __init__(self, settings: Settings):
        """Initialize LLM adapter.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._service_manager: Optional[LLMServiceManager] = None
    
    async def _get_service_manager(self) -> LLMServiceManager:
        """Get or create service manager.
        
        Returns:
            LLM service manager
        """
        if self._service_manager is None:
            self._service_manager = await get_llm_service_manager(self.settings)
        return self._service_manager
    
    def _get_model_from_settings(self) -> LLMModel:
        """Get model from settings.
        
        Returns:
            LLM model enum
        """
        model_name = getattr(self.settings, 'openai_model', 'gpt-3.5-turbo')
        
        # Map string model names to enum values
        model_mapping = {
            'gpt-3.5-turbo': LLMModel.GPT_3_5_TURBO,
            'gpt-4': LLMModel.GPT_4,
            'gpt-4-turbo-preview': LLMModel.GPT_4_TURBO,
            'gpt-4-turbo': LLMModel.GPT_4_TURBO,
            'anthropic/claude-3-opus': LLMModel.CLAUDE_3_OPUS,
            'anthropic/claude-3-sonnet': LLMModel.CLAUDE_3_SONNET,
            'meta-llama/llama-2-70b-chat': LLMModel.LLAMA_2_70B,
            'mistralai/mixtral-8x7b-instruct': LLMModel.MIXTRAL_8X7B
        }
        
        return model_mapping.get(model_name, LLMModel.GPT_3_5_TURBO)
    
    def _build_messages(self, context: ConversationContext, user_message: str) -> List[Dict[str, str]]:
        """Build messages array for LLM API.
        
        Args:
            context: Conversation context
            user_message: Latest user message
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system prompt (this logic should be moved to a prompt service)
        from .openai_service import SystemPromptTemplate
        system_prompt = SystemPromptTemplate.get_system_prompt(
            context.session_mode,
            context.user_preferences.proficiency_level,
            context.user_preferences.native_language,
            context.user_preferences.target_language
        )
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation summary if available
        if context.summary:
            summary_message = f"Previous conversation summary: {context.summary}"
            messages.append({"role": "system", "content": summary_message})
        
        # Add recent messages
        for message in context.recent_messages:
            role = "user" if message.role == MessageRole.USER else "assistant"
            messages.append({"role": role, "content": message.content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _convert_to_openai_response(self, llm_response: LLMResponse) -> OpenAIResponse:
        """Convert LLM response to OpenAI response format.
        
        Args:
            llm_response: LLM service response
            
        Returns:
            OpenAI response format
        """
        return OpenAIResponse(
            content=llm_response.content,
            model=llm_response.model,
            usage=llm_response.usage,
            finish_reason=llm_response.finish_reason,
            response_time_ms=int(llm_response.response_time_ms),
            prompt_version=llm_response.prompt_version or str(PromptVersion.V1_0)
        )
    
    async def generate_response(
        self,
        conversation_context: ConversationContext,
        user_message: str,
        prompt_version: str = str(PromptVersion.V1_0)
    ) -> OpenAIResponse:
        """Generate response using new LLM service layer.
        
        Args:
            conversation_context: Current conversation context
            user_message: Latest user message
            prompt_version: Version of prompts to use
            
        Returns:
            OpenAI response with generated content
            
        Raises:
            OpenAIServiceError: If API call fails
        """
        try:
            # Get service manager
            service_manager = await self._get_service_manager()
            
            # Build messages
            messages = self._build_messages(conversation_context, user_message)
            
            # Get model from settings
            model = self._get_model_from_settings()
            
            # Create LLM request
            native_lang = conversation_context.user_preferences.native_language
            
            llm_request = LLMRequest(
                messages=messages,
                model=model,
                max_tokens=getattr(self.settings, 'openai_max_tokens', 1000),
                temperature=getattr(self.settings, 'openai_temperature', 0.7),
                user_id=str(native_lang) if native_lang is not None else "unknown",
                prompt_version=prompt_version
            )
            
            # Generate response with automatic failover
            llm_response = await service_manager.generate_response(llm_request)
            
            # Convert to OpenAI response format
            return self._convert_to_openai_response(llm_response)
            
        except LLMServiceError as e:
            logger.error(f"LLM service error: {e}")
            raise OpenAIServiceError(f"LLM service error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in LLM adapter: {e}")
            raise OpenAIServiceError(f"Unexpected error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if LLM services are accessible.
        
        Returns:
            True if at least one service is accessible, False otherwise
        """
        try:
            service_manager = await self._get_service_manager()
            
            # Try a simple request to check availability
            test_request = LLMRequest(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"}
                ],
                model=self._get_model_from_settings(),
                max_tokens=10,
                temperature=0.1
            )
            
            await service_manager.generate_response(test_request)
            return True
            
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models.
        
        Returns:
            List of available model names
        """
        try:
            service_manager = await self._get_service_manager()
            models = service_manager.get_available_models()
            return [str(model) for model in models]
        
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    async def close(self):
        """Close LLM services."""
        if self._service_manager:
            # Close individual services if they have close methods
            for service in self._service_manager.services:
                if hasattr(service, 'close'):
                    try:
                        await service.close()
                    except Exception as e:
                        logger.error(f"Error closing service {service.provider}: {e}")


# Global adapter instance
_llm_adapter: Optional[LLMAdapter] = None


def get_llm_adapter(settings: Settings) -> LLMAdapter:
    """Get global LLM adapter instance.
    
    Args:
        settings: Application settings
        
    Returns:
        LLM adapter instance
    """
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter(settings)
    return _llm_adapter


async def cleanup_llm_adapter():
    """Cleanup global LLM adapter."""
    global _llm_adapter
    if _llm_adapter:
        await _llm_adapter.close()
        _llm_adapter = None