"""
Structured feedback entity for comprehensive language learning feedback.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from .message import CorrectionCategory


class ExtendedCorrectionCategory(Enum):
    """Extended categories for different types of corrections."""
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    STYLE = "style"
    SYNTAX = "syntax"
    SPELLING = "spelling"
    PUNCTUATION = "punctuation"
    FLUENCY = "fluency"


@dataclass
class AlternativeExpression:
    """Entity representing alternative ways to express something."""
    original: str
    alternative: str
    context: str
    formality_level: str  # formal, informal, neutral
    usage_note: Optional[str] = None
    
    def __post_init__(self):
        """Validate alternative expression data."""
        if not self.original or not self.original.strip():
            raise ValueError("Original expression cannot be empty")
        if not self.alternative or not self.alternative.strip():
            raise ValueError("Alternative expression cannot be empty")
        if not self.context or not self.context.strip():
            raise ValueError("Context cannot be empty")
        if self.formality_level not in ["formal", "informal", "neutral"]:
            raise ValueError("Formality level must be 'formal', 'informal', or 'neutral'")


@dataclass
class DetailedCorrection:
    """Entity representing detailed correction with examples and rules."""
    original: str
    correction: str
    explanation: str
    category: ExtendedCorrectionCategory
    examples: List[str]
    rule_reference: Optional[str] = None
    
    def __post_init__(self):
        """Validate detailed correction data."""
        if not self.original or not self.original.strip():
            raise ValueError("Original text cannot be empty")
        if not self.correction or not self.correction.strip():
            raise ValueError("Correction cannot be empty")
        if not self.explanation or not self.explanation.strip():
            raise ValueError("Explanation cannot be empty")
        if not isinstance(self.category, ExtendedCorrectionCategory):
            raise ValueError("Category must be a valid ExtendedCorrectionCategory")
        if not self.examples or len(self.examples) == 0:
            raise ValueError("At least one example must be provided")
        for example in self.examples:
            if not example or not example.strip():
                raise ValueError("Examples cannot be empty")


@dataclass
class GrammarFeedback:
    """Entity for grammar-specific feedback."""
    rule_name: str
    explanation: str
    correct_usage: str
    incorrect_usage: str
    additional_examples: List[str]
    difficulty_level: str  # beginner, intermediate, advanced
    
    def __post_init__(self):
        """Validate grammar feedback data."""
        if not self.rule_name or not self.rule_name.strip():
            raise ValueError("Rule name cannot be empty")
        if not self.explanation or not self.explanation.strip():
            raise ValueError("Explanation cannot be empty")
        if not self.correct_usage or not self.correct_usage.strip():
            raise ValueError("Correct usage cannot be empty")
        if not self.incorrect_usage or not self.incorrect_usage.strip():
            raise ValueError("Incorrect usage cannot be empty")
        if self.difficulty_level not in ["beginner", "intermediate", "advanced"]:
            raise ValueError("Difficulty level must be 'beginner', 'intermediate', or 'advanced'")
        for example in self.additional_examples:
            if not example or not example.strip():
                raise ValueError("Additional examples cannot be empty")


@dataclass
class StructuredFeedback:
    """Entity for comprehensive structured feedback."""
    conversation_continuation: str
    grammar_feedback: Optional[GrammarFeedback]
    error_corrections: List[DetailedCorrection]
    alternative_expressions: List[AlternativeExpression]
    native_translation: Optional[str]
    message_count: int
    overall_assessment: str
    
    def __post_init__(self):
        """Validate structured feedback data."""
        if not self.conversation_continuation or not self.conversation_continuation.strip():
            raise ValueError("Conversation continuation cannot be empty")
        if self.message_count < 1:
            raise ValueError("Message count must be at least 1")
        if not self.overall_assessment or not self.overall_assessment.strip():
            raise ValueError("Overall assessment cannot be empty")
        
        # Validate that corrections and alternatives are not empty if provided
        for correction in self.error_corrections:
            if not isinstance(correction, DetailedCorrection):
                raise ValueError("All error corrections must be DetailedCorrection instances")
        
        for alternative in self.alternative_expressions:
            if not isinstance(alternative, AlternativeExpression):
                raise ValueError("All alternative expressions must be AlternativeExpression instances")
        
        if self.grammar_feedback and not isinstance(self.grammar_feedback, GrammarFeedback):
            raise ValueError("Grammar feedback must be a GrammarFeedback instance")
    
    def has_corrections(self) -> bool:
        """Check if feedback contains any corrections."""
        return len(self.error_corrections) > 0
    
    def has_grammar_feedback(self) -> bool:
        """Check if feedback contains grammar feedback."""
        return self.grammar_feedback is not None
    
    def has_alternatives(self) -> bool:
        """Check if feedback contains alternative expressions."""
        return len(self.alternative_expressions) > 0
    
    def has_translation(self) -> bool:
        """Check if feedback contains native translation."""
        return self.native_translation is not None and self.native_translation.strip() != ""