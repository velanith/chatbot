"""AI-powered translation service implementation."""

import asyncio
import logging
import json
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from src.application.services.translation_service_interface import (
    TranslationServiceInterface,
    TranslationResult,
    LanguageDetectionResult,
    TranslationContext,
    TranslationQuality,
    LanguageDetectionConfidence,
    TranslationServiceError,
    LanguageNotSupportedError,
    TranslationQualityError,
    LanguageDetectionError
)
from src.application.services.openai_service import OpenAIService, OpenAIServiceError
from src.infrastructure.config import Settings


logger = logging.getLogger(__name__)


@dataclass
class LanguageConfig:
    """Configuration for supported languages."""
    code: str
    name: str
    native_name: str
    common_patterns: List[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.common_patterns is None:
            self.common_patterns = []


class TranslationService(TranslationServiceInterface):
    """AI-powered translation service using OpenAI."""
    
    # Supported languages with their configurations
    SUPPORTED_LANGUAGES = {
        'en': LanguageConfig('en', 'English', 'English', ['the', 'and', 'is', 'are', 'this', 'that']),
        'tr': LanguageConfig('tr', 'Turkish', 'Türkçe', ['ve', 'bir', 'bu', 'şu', 'olan', 'için']),
        'es': LanguageConfig('es', 'Spanish', 'Español', ['el', 'la', 'y', 'es', 'en', 'que']),
        'fr': LanguageConfig('fr', 'French', 'Français', ['le', 'la', 'et', 'est', 'dans', 'que']),
        'de': LanguageConfig('de', 'German', 'Deutsch', ['der', 'die', 'und', 'ist', 'in', 'das']),
        'it': LanguageConfig('it', 'Italian', 'Italiano', ['il', 'la', 'e', 'è', 'in', 'che']),
        'pt': LanguageConfig('pt', 'Portuguese', 'Português', ['o', 'a', 'e', 'é', 'em', 'que']),
        'ru': LanguageConfig('ru', 'Russian', 'Русский', ['и', 'в', 'не', 'на', 'с', 'что']),
        'zh': LanguageConfig('zh', 'Chinese', '中文', ['的', '是', '在', '了', '和', '有']),
        'ja': LanguageConfig('ja', 'Japanese', '日本語', ['の', 'に', 'は', 'を', 'が', 'で']),
        'ko': LanguageConfig('ko', 'Korean', '한국어', ['의', '에', '는', '을', '가', '로']),
        'ar': LanguageConfig('ar', 'Arabic', 'العربية', ['في', 'من', 'إلى', 'على', 'هذا', 'التي'])
    }
    
    def __init__(self, openai_service: OpenAIService, settings: Settings):
        """Initialize translation service.
        
        Args:
            openai_service: OpenAI service instance
            settings: Application settings
        """
        self.openai_service = openai_service
        self.settings = settings
        self._fallback_cache: Dict[str, TranslationResult] = {}
        self._detection_cache: Dict[str, LanguageDetectionResult] = {}
    
    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[TranslationContext] = None
    ) -> TranslationResult:
        """Translate text with context awareness and quality validation.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context for better translation
            
        Returns:
            Translation result with quality assessment
            
        Raises:
            TranslationServiceError: If translation fails
        """
        try:
            # Validate languages
            self._validate_language_support(source_language)
            self._validate_language_support(target_language)
            
            # Clean and validate input text
            cleaned_text = self._clean_text(text)
            if not cleaned_text.strip():
                return TranslationResult(
                    original_text=text,
                    translated_text="",
                    source_language=source_language,
                    target_language=target_language,
                    quality=TranslationQuality.HIGH,
                    confidence_score=1.0
                )
            
            # Check cache first
            cache_key = f"{cleaned_text}:{source_language}:{target_language}"
            if cache_key in self._fallback_cache:
                cached_result = self._fallback_cache[cache_key]
                logger.info("Using cached translation")
                return cached_result
            
            # Generate translation using AI
            translation_result = await self._generate_ai_translation(
                cleaned_text, source_language, target_language, context
            )
            
            # Validate translation quality
            quality = await self.validate_translation_quality(
                cleaned_text,
                translation_result.translated_text,
                source_language,
                target_language
            )
            
            # Update quality in result
            translation_result.quality = quality
            
            # Generate alternatives if quality is good
            if quality in [TranslationQuality.HIGH, TranslationQuality.MEDIUM]:
                try:
                    alternatives = await self.get_alternative_translations(
                        cleaned_text, source_language, target_language, count=2
                    )
                    translation_result.alternative_translations = alternatives
                except Exception as e:
                    logger.warning(f"Failed to generate alternatives: {e}")
            
            # Cache successful translation
            if quality != TranslationQuality.FAILED:
                self._fallback_cache[cache_key] = translation_result
            
            return translation_result
            
        except LanguageNotSupportedError:
            # Re-raise language support errors
            raise
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Return fallback translation
            return await self._get_fallback_translation(
                text, source_language, target_language
            )
    
    async def translate_with_context(
        self,
        text: str,
        source_language: str,
        target_language: str,
        topic_context: Optional[str] = None
    ) -> Optional[str]:
        """Translate text with additional topic context for better accuracy.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            topic_context: Optional topic context for better translation
            
        Returns:
            Translated text or None if translation fails
        """
        try:
            # Create enhanced context if topic is provided
            context = None
            if topic_context:
                context = TranslationContext(
                    domain="conversation",
                    formality_level="informal",
                    additional_context=topic_context
                )
            
            # Use existing translate_text method with context
            result = await self.translate_text(
                text, source_language, target_language, context
            )
            
            return result.translated_text if result.quality != TranslationQuality.FAILED else None
            
        except Exception as e:
            logger.error(f"Context-aware translation failed: {e}")
            return None
    
    async def detect_language(
        self,
        text: str,
        possible_languages: Optional[List[str]] = None
    ) -> LanguageDetectionResult:
        """Detect language using pattern matching and AI assistance.
        
        Args:
            text: Text to analyze
            possible_languages: Optional list of possible languages
            
        Returns:
            Language detection result
            
        Raises:
            LanguageDetectionError: If detection fails
        """
        try:
            cleaned_text = self._clean_text(text)
            if not cleaned_text.strip():
                raise LanguageDetectionError("Empty text provided")
            
            # Check cache first
            cache_key = f"detect:{cleaned_text[:100]}"
            if cache_key in self._detection_cache:
                return self._detection_cache[cache_key]
            
            # Try pattern-based detection first (fast)
            pattern_result = self._detect_language_by_patterns(
                cleaned_text, possible_languages
            )
            
            if pattern_result.confidence == LanguageDetectionConfidence.HIGH:
                self._detection_cache[cache_key] = pattern_result
                return pattern_result
            
            # Use AI for more accurate detection if pattern detection is not confident
            try:
                ai_result = await self._detect_language_with_ai(
                    cleaned_text, possible_languages
                )
            except Exception as e:
                logger.warning(f"AI detection failed, using pattern result: {e}")
                ai_result = pattern_result
            
            # Cache result
            self._detection_cache[cache_key] = ai_result
            return ai_result
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise LanguageDetectionError(f"Failed to detect language: {str(e)}")
    
    async def validate_translation_quality(
        self,
        original: str,
        translation: str,
        source_language: str,
        target_language: str
    ) -> TranslationQuality:
        """Validate translation quality using multiple criteria.
        
        Args:
            original: Original text
            translation: Translated text
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Quality assessment
        """
        try:
            # Basic validation checks
            if not translation or not translation.strip():
                return TranslationQuality.FAILED
            
            # Length ratio check (translations shouldn't be too different in length)
            length_ratio = len(translation) / max(len(original), 1)
            if length_ratio < 0.3 or length_ratio > 3.0:
                logger.warning(f"Suspicious length ratio: {length_ratio}")
                return TranslationQuality.LOW
            
            # Check if translation is just the original (no translation occurred)
            if original.strip().lower() == translation.strip().lower():
                return TranslationQuality.LOW
            
            # Use AI to assess translation quality
            quality_score = await self._assess_translation_quality_with_ai(
                original, translation, source_language, target_language
            )
            
            # Convert score to quality enum
            if quality_score >= 0.8:
                return TranslationQuality.HIGH
            elif quality_score >= 0.6:
                return TranslationQuality.MEDIUM
            elif quality_score >= 0.3:
                return TranslationQuality.LOW
            else:
                return TranslationQuality.FAILED
                
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            return TranslationQuality.MEDIUM  # Default to medium on error
    
    async def get_alternative_translations(
        self,
        text: str,
        source_language: str,
        target_language: str,
        count: int = 3
    ) -> List[str]:
        """Generate alternative translations using AI.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            count: Number of alternatives to generate
            
        Returns:
            List of alternative translations
        """
        try:
            self._validate_language_support(source_language)
            self._validate_language_support(target_language)
            
            cleaned_text = self._clean_text(text)
            if not cleaned_text.strip():
                return []
            
            # Generate alternatives using AI
            alternatives = await self._generate_alternatives_with_ai(
                cleaned_text, source_language, target_language, count
            )
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Failed to generate alternatives: {e}")
            return []
    
    async def is_native_language_text(
        self,
        text: str,
        native_language: str,
        target_language: str,
        threshold: float = 0.7
    ) -> bool:
        """Determine if text is in native language vs target language.
        
        Args:
            text: Text to check
            native_language: User's native language code
            target_language: Target learning language code
            threshold: Confidence threshold for detection
            
        Returns:
            True if text is in native language
        """
        try:
            # Detect the language of the text
            detection_result = await self.detect_language(
                text, possible_languages=[native_language, target_language]
            )
            
            # Check if detected language matches native language
            if detection_result.detected_language == native_language:
                return detection_result.confidence_score >= threshold
            
            # Also check alternative languages
            for lang_code, confidence in detection_result.alternative_languages:
                if lang_code == native_language and confidence >= threshold:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Native language detection failed: {e}")
            # Fallback: use simple pattern matching
            return self._simple_native_language_check(text, native_language, target_language)
    
    async def health_check(self) -> bool:
        """Check if translation service is healthy.
        
        Returns:
            True if service is healthy
        """
        try:
            # Test basic translation
            test_result = await self.translate_text(
                "Hello", "en", "es"
            )
            return test_result.quality != TranslationQuality.FAILED
            
        except Exception as e:
            logger.error(f"Translation service health check failed: {e}")
            return False
    
    # Private helper methods
    
    def _validate_language_support(self, language_code: str) -> None:
        """Validate that language is supported.
        
        Args:
            language_code: Language code to validate
            
        Raises:
            LanguageNotSupportedError: If language is not supported
        """
        if language_code not in self.SUPPORTED_LANGUAGES:
            raise LanguageNotSupportedError(
                f"Language '{language_code}' is not supported. "
                f"Supported languages: {list(self.SUPPORTED_LANGUAGES.keys())}"
            )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for translation.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove control characters but keep basic punctuation
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        return cleaned
    
    async def _generate_ai_translation(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[TranslationContext] = None
    ) -> TranslationResult:
        """Generate translation using AI service.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context
            
        Returns:
            Translation result
        """
        try:
            # Build translation prompt
            prompt = self._build_translation_prompt(
                text, source_language, target_language, context
            )
            
            # Create a simple conversation context for the OpenAI service
            from src.domain.entities.conversation_context import ConversationContext, UserPreferences
            from src.domain.entities.session import SessionMode, ProficiencyLevel
            
            # Create minimal context for translation
            user_prefs = UserPreferences(
                native_language=source_language,
                target_language=target_language,
                proficiency_level=ProficiencyLevel.B1
            )
            
            conv_context = ConversationContext(
                user_preferences=user_prefs,
                session_mode=SessionMode.TUTOR,
                recent_messages=[],
                summary=None
            )
            
            # Get AI response
            response = await self.openai_service.generate_response(
                conv_context, prompt
            )
            
            # Parse the response to extract translation
            translated_text = self._parse_translation_response(response.content)
            
            return TranslationResult(
                original_text=text,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                quality=TranslationQuality.HIGH,  # Will be validated separately
                confidence_score=0.9,
                context_used=context is not None
            )
            
        except Exception as e:
            logger.error(f"AI translation failed: {e}")
            raise TranslationServiceError(f"AI translation failed: {str(e)}")
    
    def _build_translation_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[TranslationContext] = None
    ) -> str:
        """Build prompt for AI translation.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context
            
        Returns:
            Translation prompt
        """
        source_lang_name = self.SUPPORTED_LANGUAGES[source_language].name
        target_lang_name = self.SUPPORTED_LANGUAGES[target_language].name
        
        prompt = f"""Translate the following text from {source_lang_name} to {target_lang_name}.

IMPORTANT: Provide ONLY the translation, no explanations or additional text.

Text to translate: "{text}"

"""
        
        # Add context if available
        if context:
            if context.conversation_topic:
                prompt += f"Context: This is part of a conversation about {context.conversation_topic}.\n"
            
            if context.user_proficiency_level:
                prompt += f"User level: {context.user_proficiency_level} level learner.\n"
            
            if context.domain:
                prompt += f"Domain: {context.domain} context.\n"
            
            if context.recent_messages:
                recent = " | ".join(context.recent_messages[-3:])
                prompt += f"Recent conversation: {recent}\n"
        
        prompt += f"\nTranslation in {target_lang_name}:"
        
        return prompt
    
    def _parse_translation_response(self, response: str) -> str:
        """Parse AI response to extract clean translation.
        
        Args:
            response: Raw AI response
            
        Returns:
            Clean translation text
        """
        # Remove common AI response prefixes/suffixes
        cleaned = response.strip()
        
        # Remove quotes if the entire response is quoted
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # Remove common prefixes
        prefixes_to_remove = [
            "Translation:", "Translated text:", "Result:", "Answer:",
            "The translation is:", "Here is the translation:"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned
    
    def _detect_language_by_patterns(
        self,
        text: str,
        possible_languages: Optional[List[str]] = None
    ) -> LanguageDetectionResult:
        """Detect language using pattern matching.
        
        Args:
            text: Text to analyze
            possible_languages: Optional list of possible languages
            
        Returns:
            Language detection result
        """
        text_lower = text.lower()
        languages_to_check = possible_languages or list(self.SUPPORTED_LANGUAGES.keys())
        
        scores = {}
        
        for lang_code in languages_to_check:
            if lang_code not in self.SUPPORTED_LANGUAGES:
                continue
                
            lang_config = self.SUPPORTED_LANGUAGES[lang_code]
            score = 0
            
            # Check for common patterns
            for pattern in lang_config.common_patterns:
                if pattern in text_lower:
                    score += 1
            
            # Normalize score by pattern count, but give bonus for multiple matches
            if lang_config.common_patterns:
                base_score = score / len(lang_config.common_patterns)
                # Give bonus for multiple pattern matches
                bonus = min(score * 0.1, 0.3)  # Up to 30% bonus
                scores[lang_code] = base_score + bonus
        
        if not scores:
            # Default to first possible language or English
            default_lang = languages_to_check[0] if languages_to_check else 'en'
            return LanguageDetectionResult(
                detected_language=default_lang,
                confidence=LanguageDetectionConfidence.LOW,
                confidence_score=0.1
            )
        
        # Find best match
        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]
        
        # Determine confidence
        if best_score >= 0.3:
            confidence = LanguageDetectionConfidence.HIGH
        elif best_score >= 0.1:
            confidence = LanguageDetectionConfidence.MEDIUM
        else:
            confidence = LanguageDetectionConfidence.LOW
        
        # Get alternatives
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        alternatives = [(lang, score) for lang, score in sorted_scores[1:4]]
        
        return LanguageDetectionResult(
            detected_language=best_lang,
            confidence=confidence,
            confidence_score=best_score,
            alternative_languages=alternatives
        )
    
    async def _detect_language_with_ai(
        self,
        text: str,
        possible_languages: Optional[List[str]] = None
    ) -> LanguageDetectionResult:
        """Detect language using AI service.
        
        Args:
            text: Text to analyze
            possible_languages: Optional list of possible languages
            
        Returns:
            Language detection result
        """
        try:
            # Build detection prompt
            languages_list = possible_languages or list(self.SUPPORTED_LANGUAGES.keys())
            lang_names = [self.SUPPORTED_LANGUAGES[code].name for code in languages_list if code in self.SUPPORTED_LANGUAGES]
            
            prompt = f"""Identify the language of the following text. 

Possible languages: {', '.join(lang_names)}

Text: "{text}"

Respond with ONLY the language code (e.g., 'en', 'tr', 'es') and confidence score (0.0-1.0) in this format:
Language: [code]
Confidence: [score]"""
            
            # Create minimal context for detection
            from src.domain.entities.conversation_context import ConversationContext, UserPreferences
            from src.domain.entities.session import SessionMode, ProficiencyLevel
            
            # Use different languages to avoid validation error
            detection_native = possible_languages[0] if possible_languages else 'en'
            detection_target = possible_languages[1] if len(possible_languages) > 1 else ('tr' if detection_native == 'en' else 'en')
            
            user_prefs = UserPreferences(
                native_language=detection_native,
                target_language=detection_target,
                proficiency_level=ProficiencyLevel.B1
            )
            
            conv_context = ConversationContext(
                user_preferences=user_prefs,
                session_mode=SessionMode.TUTOR,
                recent_messages=[],
                summary=None
            )
            
            # Get AI response
            response = await self.openai_service.generate_response(
                conv_context, prompt
            )
            
            # Parse response
            detected_lang, confidence_score = self._parse_detection_response(
                response.content, languages_list
            )
            
            # Determine confidence level
            if confidence_score >= 0.8:
                confidence = LanguageDetectionConfidence.HIGH
            elif confidence_score >= 0.6:
                confidence = LanguageDetectionConfidence.MEDIUM
            else:
                confidence = LanguageDetectionConfidence.LOW
            
            return LanguageDetectionResult(
                detected_language=detected_lang,
                confidence=confidence,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"AI language detection failed: {e}")
            # Fallback to pattern-based detection
            return self._detect_language_by_patterns(text, possible_languages)
    
    def _parse_detection_response(
        self,
        response: str,
        possible_languages: List[str]
    ) -> Tuple[str, float]:
        """Parse AI detection response.
        
        Args:
            response: AI response
            possible_languages: List of possible languages
            
        Returns:
            Tuple of (detected_language, confidence_score)
        """
        try:
            lines = response.strip().split('\n')
            detected_lang = None
            confidence_score = 0.5
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith('language:'):
                    lang_part = line.split(':', 1)[1].strip()
                    # Extract language code
                    for lang_code in possible_languages:
                        if lang_code.lower() in lang_part.lower():
                            detected_lang = lang_code
                            break
                elif line.lower().startswith('confidence:'):
                    conf_part = line.split(':', 1)[1].strip()
                    try:
                        confidence_score = float(conf_part)
                    except ValueError:
                        confidence_score = 0.5
            
            # Default to first possible language if not detected
            if not detected_lang:
                detected_lang = possible_languages[0] if possible_languages else 'en'
            
            return detected_lang, confidence_score
            
        except Exception as e:
            logger.error(f"Failed to parse detection response: {e}")
            default_lang = possible_languages[0] if possible_languages else 'en'
            return default_lang, 0.5
    
    async def _assess_translation_quality_with_ai(
        self,
        original: str,
        translation: str,
        source_language: str,
        target_language: str
    ) -> float:
        """Assess translation quality using AI.
        
        Args:
            original: Original text
            translation: Translated text
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Quality score (0.0-1.0)
        """
        try:
            source_lang_name = self.SUPPORTED_LANGUAGES[source_language].name
            target_lang_name = self.SUPPORTED_LANGUAGES[target_language].name
            
            prompt = f"""Assess the quality of this translation from {source_lang_name} to {target_lang_name}.

Original ({source_lang_name}): "{original}"
Translation ({target_lang_name}): "{translation}"

Rate the translation quality on a scale of 0.0 to 1.0 considering:
- Accuracy of meaning
- Grammar correctness
- Natural fluency
- Context appropriateness

Respond with ONLY a number between 0.0 and 1.0."""
            
            # Create minimal context
            from src.domain.entities.conversation_context import ConversationContext, UserPreferences
            from src.domain.entities.session import SessionMode, ProficiencyLevel
            
            user_prefs = UserPreferences(
                native_language=source_language,
                target_language=target_language,
                proficiency_level=ProficiencyLevel.B1
            )
            
            conv_context = ConversationContext(
                user_preferences=user_prefs,
                session_mode=SessionMode.TUTOR,
                recent_messages=[],
                summary=None
            )
            
            # Get AI response
            response = await self.openai_service.generate_response(
                conv_context, prompt
            )
            
            # Parse quality score
            try:
                score = float(response.content.strip())
                return max(0.0, min(1.0, score))  # Clamp to valid range
            except ValueError:
                logger.warning(f"Invalid quality score response: {response.content}")
                return 0.7  # Default to medium quality
                
        except Exception as e:
            logger.error(f"AI quality assessment failed: {e}")
            return 0.7  # Default to medium quality
    
    async def _generate_alternatives_with_ai(
        self,
        text: str,
        source_language: str,
        target_language: str,
        count: int
    ) -> List[str]:
        """Generate alternative translations using AI.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            count: Number of alternatives
            
        Returns:
            List of alternative translations
        """
        try:
            source_lang_name = self.SUPPORTED_LANGUAGES[source_language].name
            target_lang_name = self.SUPPORTED_LANGUAGES[target_language].name
            
            prompt = f"""Provide {count} different ways to translate this text from {source_lang_name} to {target_lang_name}.

Text: "{text}"

Provide {count} alternative translations, each on a separate line:
1. [translation 1]
2. [translation 2]
3. [translation 3]

Focus on different styles (formal/informal) or word choices while maintaining the same meaning."""
            
            # Create minimal context
            from src.domain.entities.conversation_context import ConversationContext, UserPreferences
            from src.domain.entities.session import SessionMode, ProficiencyLevel
            
            user_prefs = UserPreferences(
                native_language=source_language,
                target_language=target_language,
                proficiency_level=ProficiencyLevel.B1
            )
            
            conv_context = ConversationContext(
                user_preferences=user_prefs,
                session_mode=SessionMode.TUTOR,
                recent_messages=[],
                summary=None
            )
            
            # Get AI response
            response = await self.openai_service.generate_response(
                conv_context, prompt
            )
            
            # Parse alternatives
            alternatives = []
            lines = response.content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering/bullets
                    clean_line = re.sub(r'^\d+\.\s*', '', line)
                    clean_line = re.sub(r'^-\s*', '', clean_line)
                    clean_line = clean_line.strip()
                    
                    if clean_line and clean_line not in alternatives:
                        alternatives.append(clean_line)
            
            return alternatives[:count]
            
        except Exception as e:
            logger.error(f"Failed to generate alternatives: {e}")
            return []
    
    def _simple_native_language_check(
        self,
        text: str,
        native_language: str,
        target_language: str
    ) -> bool:
        """Simple fallback check for native language detection.
        
        Args:
            text: Text to check
            native_language: Native language code
            target_language: Target language code
            
        Returns:
            True if likely native language
        """
        try:
            if native_language not in self.SUPPORTED_LANGUAGES:
                return False
            
            native_patterns = self.SUPPORTED_LANGUAGES[native_language].common_patterns
            target_patterns = self.SUPPORTED_LANGUAGES.get(target_language, LanguageConfig('', '', '')).common_patterns
            
            text_lower = text.lower()
            
            native_matches = sum(1 for pattern in native_patterns if pattern in text_lower)
            target_matches = sum(1 for pattern in target_patterns if pattern in text_lower)
            
            # If more native patterns match, likely native language
            return native_matches > target_matches
            
        except Exception as e:
            logger.error(f"Simple native language check failed: {e}")
            return False
    
    async def _get_fallback_translation(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> TranslationResult:
        """Get fallback translation when AI fails.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Fallback translation result
        """
        # Simple fallback: return original text with low quality
        return TranslationResult(
            original_text=text,
            translated_text=f"[Translation unavailable: {text}]",
            source_language=source_language,
            target_language=target_language,
            quality=TranslationQuality.FAILED,
            confidence_score=0.0
        )