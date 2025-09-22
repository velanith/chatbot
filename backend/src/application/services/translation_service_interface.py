"""Translation service interface for language learning platform."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class TranslationQuality(str, Enum):
    """Translation quality levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    FAILED = "failed"


class LanguageDetectionConfidence(str, Enum):
    """Language detection confidence levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    quality: TranslationQuality
    confidence_score: float
    alternative_translations: List[str] = None
    context_used: bool = False
    
    def __post_init__(self):
        """Initialize default values."""
        if self.alternative_translations is None:
            self.alternative_translations = []


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    detected_language: str
    confidence: LanguageDetectionConfidence
    confidence_score: float
    alternative_languages: List[Tuple[str, float]] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.alternative_languages is None:
            self.alternative_languages = []


@dataclass
class TranslationContext:
    """Context information for better translation quality."""
    conversation_topic: Optional[str] = None
    user_proficiency_level: Optional[str] = None
    recent_messages: List[str] = None
    domain: Optional[str] = None  # e.g., "education", "casual", "business"
    
    def __post_init__(self):
        """Initialize default values."""
        if self.recent_messages is None:
            self.recent_messages = []


class TranslationServiceInterface(ABC):
    """Interface for translation services."""
    
    @abstractmethod
    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[TranslationContext] = None
    ) -> TranslationResult:
        """Translate text from source to target language.
        
        Args:
            text: Text to translate
            source_language: Source language code (e.g., 'tr', 'en')
            target_language: Target language code (e.g., 'en', 'es')
            context: Optional context for better translation
            
        Returns:
            Translation result with quality assessment
            
        Raises:
            TranslationServiceError: If translation fails
        """
        pass
    
    @abstractmethod
    async def detect_language(
        self,
        text: str,
        possible_languages: Optional[List[str]] = None
    ) -> LanguageDetectionResult:
        """Detect the language of given text.
        
        Args:
            text: Text to analyze
            possible_languages: Optional list of possible languages to check
            
        Returns:
            Language detection result
            
        Raises:
            TranslationServiceError: If detection fails
        """
        pass
    
    @abstractmethod
    async def validate_translation_quality(
        self,
        original: str,
        translation: str,
        source_language: str,
        target_language: str
    ) -> TranslationQuality:
        """Validate the quality of a translation.
        
        Args:
            original: Original text
            translation: Translated text
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Quality assessment
            
        Raises:
            TranslationServiceError: If validation fails
        """
        pass
    
    @abstractmethod
    async def get_alternative_translations(
        self,
        text: str,
        source_language: str,
        target_language: str,
        count: int = 3
    ) -> List[str]:
        """Get alternative translations for the same text.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            count: Number of alternatives to generate
            
        Returns:
            List of alternative translations
            
        Raises:
            TranslationServiceError: If generation fails
        """
        pass
    
    @abstractmethod
    async def is_native_language_text(
        self,
        text: str,
        native_language: str,
        target_language: str,
        threshold: float = 0.7
    ) -> bool:
        """Check if text is written in native language vs target language.
        
        Args:
            text: Text to check
            native_language: User's native language code
            target_language: Target learning language code
            threshold: Confidence threshold for detection
            
        Returns:
            True if text is in native language, False otherwise
            
        Raises:
            TranslationServiceError: If detection fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the translation service is available.
        
        Returns:
            True if service is healthy, False otherwise
        """
        pass


class TranslationServiceError(Exception):
    """Base exception for translation service errors."""
    pass


class LanguageNotSupportedError(TranslationServiceError):
    """Raised when a language is not supported."""
    pass


class TranslationQualityError(TranslationServiceError):
    """Raised when translation quality is too low."""
    pass


class LanguageDetectionError(TranslationServiceError):
    """Raised when language detection fails."""
    pass