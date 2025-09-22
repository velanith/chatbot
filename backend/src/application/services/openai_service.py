"""OpenAI service for Polyglot language learning platform."""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import aiohttp
from datetime import datetime

from src.domain.entities.session import SessionMode, ProficiencyLevel
from src.domain.entities.message import Message, MessageRole
from src.domain.entities.conversation_context import ConversationContext
from src.infrastructure.config import Settings


logger = logging.getLogger(__name__)


class PromptVersion(str, Enum):
    """Prompt version for tracking."""
    V1_0 = "v1.0"
    V1_1 = "v1.1"


@dataclass
class OpenAIRequest:
    """OpenAI API request data structure."""
    
    messages: List[Dict[str, str]]
    model: str
    max_tokens: int
    temperature: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    prompt_version: str = PromptVersion.V1_0.value


@dataclass
class OpenAIResponse:
    """OpenAI API response data structure."""
    
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time_ms: int
    prompt_version: str


class OpenAIServiceError(Exception):
    """Base exception for OpenAI service errors."""
    pass


class OpenAIAPIError(OpenAIServiceError):
    """OpenAI API specific errors."""
    
    def __init__(self, message: str, status_code: int = None, error_type: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type


class OpenAIRateLimitError(OpenAIServiceError):
    """Rate limit exceeded error."""
    pass


class OpenAITimeoutError(OpenAIServiceError):
    """Request timeout error."""
    pass


class SystemPromptTemplate:
    """System prompt templates for different modes and levels."""
    
    TUTOR_PROMPTS = {
        ProficiencyLevel.A1: """You are a friendly English tutor helping a beginner (A1 level) Turkish speaker learn English. 

IMPORTANT CORRECTION FORMAT:
When the student makes mistakes, provide corrections in this EXACT format:
**Original:** "[original text]"
**Corrected:** "[corrected text in English]"
**Explanation:** "[brief explanation in Turkish about why it's wrong]"

Then continue with your teaching response in English.

Guidelines:
- Always start conversations with a warm greeting in English
- Use simple, clear English (max 3-6 sentences per response)
- Provide gentle corrections for grammar/vocabulary mistakes (max 1 correction per message)
- Use basic vocabulary and short sentences
- Be encouraging and patient
- Focus on practical, everyday topics
- Always respond in English, but correction explanations can be in Turkish for clarity

Your student's native language is Turkish, so you understand their common mistakes. Help them build confidence while learning.""",

        ProficiencyLevel.A2: """You are a supportive English tutor helping an elementary (A2 level) Turkish speaker improve their English.

IMPORTANT CORRECTION FORMAT:
When the student makes mistakes, provide corrections in this EXACT format:
**Original:** "[original text]"
**Corrected:** "[corrected text in English]"
**Explanation:** "[brief explanation in Turkish about why it's wrong]"

Then continue with your teaching response in English.

Guidelines:
- Always start conversations with a warm greeting in English
- Use clear, simple English (3-6 sentences per response)
- Provide helpful corrections for mistakes (max 1 correction per message)
- Use elementary vocabulary with some new words
- Be encouraging and constructive
- Introduce slightly more complex grammar gradually
- Always respond in English, but correction explanations can be in Turkish for clarity

Your student has basic English knowledge. Help them expand their vocabulary and improve their grammar naturally.""",

        ProficiencyLevel.B1: """You are an encouraging English tutor helping an intermediate (B1 level) Turkish speaker advance their English skills.

IMPORTANT CORRECTION FORMAT:
When the student makes mistakes, provide corrections in this EXACT format:
**Original:** "[original text]"
**Corrected:** "[corrected text in English]"
**Explanation:** "[brief explanation in Turkish about why it's wrong]"

Then continue with your teaching response in English.

Guidelines:
- Always start conversations with a warm greeting in English
- Use natural English (3-6 sentences per response)
- Provide constructive corrections (max 1 correction per message)
- Use intermediate vocabulary and introduce advanced words
- Be supportive while challenging them appropriately
- Help with more complex grammar and expressions
- Always respond in English, but correction explanations can be in Turkish for clarity

Your student can handle intermediate conversations. Help them refine their skills and build fluency."""
    }
    
    BUDDY_PROMPTS = {
        ProficiencyLevel.A1: """You are a friendly English conversation partner chatting with a beginner (A1 level) Turkish speaker.

Guidelines:
- Always start conversations with a warm greeting in English
- Use simple, natural English (3-6 sentences per response)
- Don't correct mistakes - just have a natural conversation
- Use basic vocabulary and short sentences
- Be casual, friendly, and encouraging
- Talk about everyday topics and interests
- Always respond in English

Just be a supportive friend helping them practice English naturally through conversation.""",

        ProficiencyLevel.A2: """You are a friendly English conversation partner chatting with an elementary (A2 level) Turkish speaker.

Guidelines:
- Always start conversations with a warm greeting in English
- Use clear, natural English (3-6 sentences per response)
- Don't focus on corrections - prioritize natural conversation flow
- Use elementary vocabulary with occasional new words
- Be casual, friendly, and engaging
- Discuss everyday topics and shared interests
- Always respond in English

Be a supportive conversation partner helping them gain confidence in English.""",

        ProficiencyLevel.B1: """You are a friendly English conversation partner chatting with an intermediate (B1 level) Turkish speaker.

Guidelines:
- Always start conversations with a warm greeting in English
- Use natural, conversational English (3-6 sentences per response)
- Focus on natural conversation flow, not corrections
- Use intermediate vocabulary naturally
- Be engaging, friendly, and authentic
- Discuss various topics and interests
- Always respond in English

Be a genuine conversation partner helping them practice English in a relaxed, natural way."""
    }
    
    @classmethod
    def get_system_prompt(cls, mode: SessionMode, level: ProficiencyLevel, native_language: str = 'tr', target_language: str = 'en') -> str:
        """Get system prompt for given mode and level."""
        base_prompt = ""
        if mode == SessionMode.TUTOR:
            base_prompt = cls.TUTOR_PROMPTS.get(level, cls.TUTOR_PROMPTS[ProficiencyLevel.A2])
        else:
            base_prompt = cls.BUDDY_PROMPTS.get(level, cls.BUDDY_PROMPTS[ProficiencyLevel.A2])
        
        # Replace language placeholders
        language_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'tr': 'Turkish', 'ar': 'Arabic',
            'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ru': 'Russian'
        }
        
        # Ensure language codes are strings
        native_language_str = str(native_language) if native_language is not None else 'tr'
        target_language_str = str(target_language) if target_language is not None else 'en'
        
        native_lang_name = language_names.get(native_language_str.lower(), 'Turkish')
        target_lang_name = language_names.get(target_language_str.lower(), 'English')
        
        # Create a completely new prompt for the target language
        if target_language_str.lower() != 'en':
            # For non-English target languages, create a custom prompt
            if mode == SessionMode.TUTOR:
                prompt = f"""You are a friendly {target_lang_name} tutor helping a {level.value} level {native_lang_name} speaker learn {target_lang_name}.

CRITICAL: You must respond ONLY in {target_lang_name}. Never use {native_lang_name} or any other language.

IMPORTANT CORRECTION FORMAT:
When the student makes mistakes, provide corrections in this EXACT format:
**Original:** "[original text]"
**Corrected:** "[corrected text in {target_lang_name}]"
**Explanation:** "[brief explanation in {native_lang_name} about why it's wrong]"

Then continue with your teaching response in {target_lang_name}.

Guidelines:
- Always start conversations with a warm greeting in {target_lang_name}
- Use simple, clear {target_lang_name} appropriate for {level.value} level
- Provide gentle corrections for grammar/vocabulary mistakes (max 1 correction per message)
- Be encouraging and patient
- Focus on practical, everyday topics
- Always respond in {target_lang_name}, but explanations can be in {native_lang_name} for clarity

Your student's native language is {native_lang_name}, so you understand their common mistakes. Help them build confidence while learning {target_lang_name}.

REMINDER: All conversation must be in {target_lang_name}, but correction explanations can be in {native_lang_name}."""
            else:
                prompt = f"""You are a friendly {target_lang_name} conversation partner chatting with a {level.value} level {native_lang_name} speaker.

CRITICAL: You must respond ONLY in {target_lang_name}. Never use {native_lang_name} or any other language.

Guidelines:
- Always start conversations with a warm greeting in {target_lang_name}
- Use natural, conversational {target_lang_name} appropriate for {level.value} level
- Don't focus on corrections - prioritize natural conversation flow
- Be casual, friendly, and engaging
- Discuss everyday topics and shared interests
- Always respond in {target_lang_name}

Be a supportive conversation partner helping them practice {target_lang_name} naturally.

REMINDER: All your responses must be in {target_lang_name}."""
            logger.info(f"DEBUG: Using custom prompt for {target_lang_name}")
        else:
            logger.info(f"DEBUG: Using English prompt")
            # For English target language, use the original prompt with replacements
            replacements = [
                ('Turkish speaker learn English', f'{native_lang_name} speaker learn {target_lang_name}'),
                ('Turkish speaker improve their English', f'{native_lang_name} speaker improve their {target_lang_name}'),
                ('Turkish speaker advance their English skills', f'{native_lang_name} speaker advance their {target_lang_name} skills'),
                ('native language is Turkish', f'native language is {native_lang_name}'),
                ('Always respond in English', f'Always respond in {target_lang_name}'),
                ('English tutor', f'{target_lang_name} tutor'),
                ('Turkish', native_lang_name)
            ]
            
            prompt = base_prompt
            for old, new in replacements:
                prompt = prompt.replace(old, new)
        
        logger.info(f"DEBUG: Final prompt: {prompt[:200]}...")
        return prompt


class OpenAIService:
    """Service for OpenAI API integration."""
    
    def __init__(self, settings: Settings):
        """Initialize OpenAI service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.session = None
        self._session_setup = False
    
    async def _setup_session(self):
        """Setup aiohttp session with proper headers."""
        if self._session_setup:
            return
            
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Polyglot/1.0"
        }
        
        if self.settings.use_openrouter:
            headers["Authorization"] = f"Bearer {self.settings.openrouter_api_key}"
            headers["HTTP-Referer"] = "https://github.com/your-repo"  # Required by OpenRouter
            headers["X-Title"] = "Polyglot"
            self.base_url = self.settings.openrouter_base_url
        else:
            headers["Authorization"] = f"Bearer {self.settings.openai_api_key}"
            self.base_url = self.settings.openai_base_url
        
        timeout = aiohttp.ClientTimeout(total=self.settings.openai_timeout)
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout
        )
        self._session_setup = True
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def generate_response(
        self,
        conversation_context: ConversationContext,
        user_message: str,
        prompt_version: str = PromptVersion.V1_0.value
    ) -> OpenAIResponse:
        """Generate response using OpenAI API.
        
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
            # Ensure session is setup
            await self._setup_session()
            
            # Build messages for API call
            messages = self._build_messages(conversation_context, user_message)
            
            # Create request
            request = OpenAIRequest(
                messages=messages,
                model=self.settings.openai_model,
                max_tokens=self.settings.openai_max_tokens,
                temperature=self.settings.openai_temperature,
                user_id=str(conversation_context.user_preferences.native_language),
                prompt_version=prompt_version
            )
            
            # Make API call with retries
            response = await self._make_api_call_with_retries(request)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise OpenAIServiceError(f"Failed to generate response: {str(e)}")
    
    def _build_messages(self, context: ConversationContext, user_message: str) -> List[Dict[str, str]]:
        """Build messages array for OpenAI API.
        
        Args:
            context: Conversation context
            user_message: Latest user message
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system prompt
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
    
    async def _make_api_call_with_retries(self, request: OpenAIRequest) -> OpenAIResponse:
        """Make API call with exponential backoff retries.
        
        Args:
            request: OpenAI request data
            
        Returns:
            OpenAI response
            
        Raises:
            OpenAIServiceError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.settings.openai_max_retries):
            try:
                return await self._make_api_call(request)
                
            except OpenAIRateLimitError as e:
                last_exception = e
                if attempt < self.settings.openai_max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, etc.
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except OpenAITimeoutError as e:
                last_exception = e
                if attempt < self.settings.openai_max_retries - 1:
                    wait_time = 1 + attempt
                    logger.warning(f"Timeout, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except OpenAIAPIError as e:
                # Don't retry on client errors (4xx)
                if e.status_code and 400 <= e.status_code < 500:
                    raise
                
                last_exception = e
                if attempt < self.settings.openai_max_retries - 1:
                    wait_time = 1 + attempt
                    logger.warning(f"API error, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
        
        # All retries failed
        raise last_exception or OpenAIServiceError("All retries failed")
    
    async def _make_api_call(self, request: OpenAIRequest) -> OpenAIResponse:
        """Make single API call to OpenAI.
        
        Args:
            request: OpenAI request data
            
        Returns:
            OpenAI response
            
        Raises:
            OpenAIServiceError: If API call fails
        """
        start_time = datetime.now()
        
        try:
            # Prepare request data
            data = {
                "model": request.model,
                "messages": request.messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            
            # Add custom headers
            headers = {}
            if request.prompt_version:
                headers["X-Prompt-Version"] = request.prompt_version
            
            # Make API call
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=data,
                headers=headers
            ) as response:
                response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                if response.status == 429:
                    raise OpenAIRateLimitError("Rate limit exceeded")
                
                if response.status == 408 or response.status == 524:
                    raise OpenAITimeoutError("Request timeout")
                
                response_data = await response.json()
                
                if response.status != 200:
                    error_message = response_data.get("error", {}).get("message", "Unknown error")
                    error_type = response_data.get("error", {}).get("type", "unknown")
                    raise OpenAIAPIError(
                        f"API error: {error_message}",
                        status_code=response.status,
                        error_type=error_type
                    )
                
                # Parse successful response
                choice = response_data["choices"][0]
                content = choice["message"]["content"]
                
                return OpenAIResponse(
                    content=content,
                    model=response_data["model"],
                    usage=response_data.get("usage", {}),
                    finish_reason=choice.get("finish_reason", "unknown"),
                    response_time_ms=response_time_ms,
                    prompt_version=request.prompt_version
                )
                
        except aiohttp.ClientError as e:
            raise OpenAITimeoutError(f"Network error: {str(e)}")
        
        except json.JSONDecodeError as e:
            raise OpenAIAPIError(f"Invalid JSON response: {str(e)}")
        
        except Exception as e:
            if isinstance(e, OpenAIServiceError):
                raise
            raise OpenAIServiceError(f"Unexpected error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Ensure session is setup
            await self._setup_session()
            
            # Simple test request
            test_messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"}
            ]
            
            request = OpenAIRequest(
                messages=test_messages,
                model=self.settings.openai_model,
                max_tokens=10,
                temperature=0.1
            )
            
            await self._make_api_call(request)
            return True
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False