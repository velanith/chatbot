"""Pedagogy engine for educational response optimization."""

import re
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.domain.entities.message import Message, MessageRole, Correction, CorrectionCategory
from src.domain.entities.session import Session, SessionMode, ProficiencyLevel
from src.domain.entities.conversation_context import ConversationContext, UserPreferences
from src.domain.entities.structured_feedback import (
    StructuredFeedback, 
    DetailedCorrection, 
    AlternativeExpression, 
    GrammarFeedback,
    ExtendedCorrectionCategory
)


logger = logging.getLogger(__name__)


@dataclass
class PedagogicalConstraints:
    """Configuration for pedagogical constraints."""
    min_response_sentences: int = 3
    max_response_sentences: int = 6
    max_corrections_per_message: int = 3
    micro_exercise_frequency: int = 5  # Every N messages
    correction_priority_weights: Dict[CorrectionCategory, float] = None
    
    def __post_init__(self):
        """Initialize default correction priority weights."""
        if self.correction_priority_weights is None:
            self.correction_priority_weights = {
                CorrectionCategory.GRAMMAR: 1.0,
                CorrectionCategory.VOCABULARY: 0.8,
                CorrectionCategory.PRONUNCIATION: 0.6,
                CorrectionCategory.STYLE: 0.4
            }


@dataclass
class PedagogicalResponse:
    """Structured pedagogical response."""
    formatted_response: str
    selected_corrections: List[Correction]
    micro_exercise: Optional[str]
    response_metadata: Dict[str, any]


class ResponseFormatter:
    """Formats AI responses according to pedagogical constraints."""
    
    def __init__(self, constraints: PedagogicalConstraints):
        """Initialize response formatter.
        
        Args:
            constraints: Pedagogical constraints configuration
        """
        self.constraints = constraints
    
    def format_response(self, raw_response: str, proficiency_level: ProficiencyLevel) -> str:
        """Format response according to length and complexity constraints.
        
        Args:
            raw_response: Raw AI response
            proficiency_level: User's proficiency level
            
        Returns:
            Formatted response within pedagogical constraints
        """
        # Clean response by removing correction lines
        cleaned_response = self._remove_correction_lines(raw_response)
        
        # Split into sentences
        sentences = self._split_into_sentences(cleaned_response)
        
        # Apply length constraints
        if len(sentences) < self.constraints.min_response_sentences:
            # Response too short - pad with encouraging phrases
            sentences = self._pad_short_response(sentences, proficiency_level)
        elif len(sentences) > self.constraints.max_response_sentences:
            # Response too long - trim while preserving meaning
            sentences = self._trim_long_response(sentences)
        
        # Adjust complexity based on proficiency level
        sentences = self._adjust_complexity(sentences, proficiency_level)
        
        # Join sentences with proper punctuation
        result = []
        for sentence in sentences:
            if sentence and not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            result.append(sentence)
        
        return ' '.join(result)
    
    def _remove_correction_lines(self, text: str) -> str:
        """Remove correction lines from AI response.
        
        Args:
            text: Raw AI response
            
        Returns:
            Cleaned response without correction lines
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines that start with "Correction:"
            if line.startswith('Correction:'):
                continue
            # Skip empty lines after corrections
            if not line and cleaned_lines and not cleaned_lines[-1]:
                continue
            cleaned_lines.append(line)
        
        # Join lines and clean up extra whitespace
        result = '\n'.join(cleaned_lines).strip()
        # Remove multiple consecutive newlines
        result = re.sub(r'\n\s*\n', '\n\n', result)
        return result
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with NLP libraries)
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _pad_short_response(self, sentences: List[str], proficiency_level: ProficiencyLevel) -> List[str]:
        """Pad short responses with appropriate phrases.
        
        Args:
            sentences: Current sentences
            proficiency_level: User's proficiency level
            
        Returns:
            Padded sentences
        """
        padding_phrases = {
            ProficiencyLevel.A1: [
                "Keep practicing!",
                "You're doing great!",
                "Let's continue learning together."
            ],
            ProficiencyLevel.A2: [
                "That's a good question!",
                "You're making good progress.",
                "Let me help you with this."
            ],
            ProficiencyLevel.B1: [
                "That's an interesting point.",
                "I can see you're thinking carefully about this.",
                "Let's explore this topic further."
            ]
        }
        
        needed = self.constraints.min_response_sentences - len(sentences)
        available_phrases = padding_phrases.get(proficiency_level, padding_phrases[ProficiencyLevel.A2])
        
        for i in range(min(needed, len(available_phrases))):
            sentences.append(available_phrases[i])
        
        return sentences
    
    def _trim_long_response(self, sentences: List[str]) -> List[str]:
        """Trim long responses while preserving key information.
        
        Args:
            sentences: Current sentences
            
        Returns:
            Trimmed sentences
        """
        if len(sentences) <= self.constraints.max_response_sentences:
            return sentences
        
        # Keep first and last sentences, trim middle
        keep_count = self.constraints.max_response_sentences
        if keep_count >= 2:
            # Keep first sentence, last sentence, and best middle sentences
            first = sentences[0]
            last = sentences[-1]
            middle_count = keep_count - 2
            
            if middle_count > 0:
                middle_sentences = sentences[1:-1]
                # Simple heuristic: prefer shorter, more direct sentences
                middle_sentences.sort(key=len)
                selected_middle = middle_sentences[:middle_count]
                return [first] + selected_middle + [last]
            else:
                return [first, last]
        else:
            # Just keep the first N sentences
            return sentences[:keep_count]
    
    def _adjust_complexity(self, sentences: List[str], proficiency_level: ProficiencyLevel) -> List[str]:
        """Adjust sentence complexity based on proficiency level.
        
        Args:
            sentences: Current sentences
            proficiency_level: User's proficiency level
            
        Returns:
            Complexity-adjusted sentences
        """
        # For now, return as-is. In a full implementation, this could:
        # - Simplify vocabulary for lower levels
        # - Break complex sentences into simpler ones
        # - Add explanatory phrases for difficult concepts
        return sentences


class CorrectionSelector:
    """Selects and prioritizes corrections for pedagogical effectiveness."""
    
    def __init__(self, constraints: PedagogicalConstraints):
        """Initialize correction selector.
        
        Args:
            constraints: Pedagogical constraints configuration
        """
        self.constraints = constraints
    
    def select_corrections(
        self,
        all_corrections: List[Correction],
        proficiency_level: ProficiencyLevel,
        recent_corrections: List[Correction] = None
    ) -> List[Correction]:
        """Select most pedagogically valuable corrections.
        
        Args:
            all_corrections: All available corrections
            proficiency_level: User's proficiency level
            recent_corrections: Recent corrections to avoid repetition
            
        Returns:
            Selected corrections (max 3)
        """
        if not all_corrections:
            return []
        
        recent_corrections = recent_corrections or []
        
        # Score corrections based on pedagogical value
        scored_corrections = []
        for correction in all_corrections:
            score = self._calculate_correction_score(
                correction, proficiency_level, recent_corrections
            )
            scored_corrections.append((correction, score))
        
        # Sort by score (highest first) and take top N
        scored_corrections.sort(key=lambda x: x[1], reverse=True)
        selected = [corr for corr, score in scored_corrections[:self.constraints.max_corrections_per_message]]
        
        logger.info(f"Selected {len(selected)} corrections from {len(all_corrections)} available")
        return selected
    
    def _calculate_correction_score(
        self,
        correction: Correction,
        proficiency_level: ProficiencyLevel,
        recent_corrections: List[Correction]
    ) -> float:
        """Calculate pedagogical score for a correction.
        
        Args:
            correction: Correction to score
            proficiency_level: User's proficiency level
            recent_corrections: Recent corrections for deduplication
            
        Returns:
            Pedagogical score (higher is better)
        """
        score = 0.0
        
        # Base score from category priority
        category_weight = self.constraints.correction_priority_weights.get(
            correction.category, 0.5
        )
        score += category_weight
        
        # Proficiency level adjustments
        if proficiency_level in [ProficiencyLevel.A1, ProficiencyLevel.A2]:
            # Beginners: prioritize grammar and basic vocabulary
            if correction.category in [CorrectionCategory.GRAMMAR, CorrectionCategory.VOCABULARY]:
                score += 0.3
        elif proficiency_level == ProficiencyLevel.B1:
            # Intermediate: balance all types, slight preference for style
            if correction.category == CorrectionCategory.STYLE:
                score += 0.2
            else:
                score += 0.1
        
        # Penalty for recent repetition
        for recent in recent_corrections[-5:]:  # Check last 5 corrections
            if (correction.original.lower() == recent.original.lower() or
                correction.category == recent.category):
                score -= 0.2
        
        # Length penalty for very long explanations (keep it simple)
        if len(correction.explanation) > 100:
            score -= 0.1
        
        return max(0.0, score)


class MicroExerciseGenerator:
    """Generates micro-exercises based on conversation context."""
    
    def __init__(self, constraints: PedagogicalConstraints):
        """Initialize micro-exercise generator.
        
        Args:
            constraints: Pedagogical constraints configuration
        """
        self.constraints = constraints
    
    def should_generate_exercise(
        self,
        message_count: int,
        recent_corrections: List[Correction],
        last_exercise_message: Optional[int] = None
    ) -> bool:
        """Determine if a micro-exercise should be generated.
        
        Args:
            message_count: Current message count in session
            recent_corrections: Recent corrections made
            last_exercise_message: Message number of last exercise
            
        Returns:
            True if exercise should be generated
        """
        # Check frequency constraint
        if last_exercise_message is not None:
            messages_since_last = message_count - last_exercise_message
            if messages_since_last < self.constraints.micro_exercise_frequency:
                return False
        
        # Need at least one correction to base exercise on
        if not recent_corrections:
            return False
        
        # Generate exercise every N messages if there are corrections
        return message_count % self.constraints.micro_exercise_frequency == 0
    
    def generate_exercise_prompt(
        self,
        recent_corrections: List[Correction],
        proficiency_level: ProficiencyLevel,
        conversation_topic: Optional[str] = None
    ) -> str:
        """Generate prompt for micro-exercise creation.
        
        Args:
            recent_corrections: Recent corrections to base exercise on
            proficiency_level: User's proficiency level
            conversation_topic: Current conversation topic
            
        Returns:
            Exercise prompt for AI generation
        """
        if not recent_corrections:
            return ""
        
        # Focus on most recent and important corrections
        key_corrections = recent_corrections[-2:]  # Last 2 corrections
        
        correction_summary = []
        for corr in key_corrections:
            correction_summary.append(
                f"- {corr.original} → {corr.correction} ({str(corr.category)})"
            )
        
        topic_context = f" related to {conversation_topic}" if conversation_topic else ""
        
        exercise_prompt = f"""
Create a quick practice exercise (1-2 minutes) based on these recent corrections:

{chr(10).join(correction_summary)}

Requirements:
- Proficiency level: {str(proficiency_level)}
- Make it practical and engaging{topic_context}
- Focus on the corrected grammar/vocabulary patterns
- Provide clear instructions
- Keep it short and focused

Generate just the exercise text, no additional explanation.
"""
        
        return exercise_prompt.strip()


class StructuredFeedbackGenerator:
    """Generates structured feedback for 3-message cycles."""
    
    def __init__(self, constraints: PedagogicalConstraints):
        """Initialize structured feedback generator.
        
        Args:
            constraints: Pedagogical constraints configuration
        """
        self.constraints = constraints
        self._translation_service = None
    
    def set_translation_service(self, translation_service):
        """Set the translation service for enhanced native language support.
        
        Args:
            translation_service: Translation service instance
        """
        self._translation_service = translation_service
    
    def should_provide_structured_feedback(self, message_count: int, last_feedback_message: Optional[int] = None) -> bool:
        """Determine if structured feedback should be provided.
        
        Args:
            message_count: Current message count in session
            last_feedback_message: Message number of last structured feedback
            
        Returns:
            True if structured feedback should be provided
        """
        # Provide feedback every 3 messages
        if last_feedback_message is None:
            return message_count >= 3 and message_count % 3 == 0
        
        messages_since_last = message_count - last_feedback_message
        return messages_since_last >= 3
    
    async def generate_structured_feedback(
        self,
        recent_messages: List[Message],
        corrections: List[Correction],
        proficiency_level: ProficiencyLevel,
        native_language: str = "TR",
        target_language: str = "EN",
        current_topic: Optional[str] = None
    ) -> StructuredFeedback:
        """Generate comprehensive structured feedback.
        
        Args:
            recent_messages: Last 3 user messages for analysis
            corrections: Available corrections from the messages
            proficiency_level: User's proficiency level
            native_language: User's native language
            target_language: Target learning language
            current_topic: Current conversation topic
            
        Returns:
            Structured feedback with all components
        """
        # Generate conversation continuation
        continuation = self._generate_conversation_continuation(
            recent_messages, proficiency_level, current_topic
        )
        
        # Convert corrections to detailed corrections
        detailed_corrections = self._create_detailed_corrections(corrections, proficiency_level)
        
        # Generate alternative expressions
        alternatives = self._generate_alternative_expressions(
            recent_messages, proficiency_level, target_language
        )
        
        # Generate grammar feedback if applicable
        grammar_feedback = self._generate_grammar_feedback(
            corrections, proficiency_level, target_language
        )
        
        # Generate native translation if needed
        native_translation = await self._generate_native_translation(
            recent_messages, native_language, target_language
        )
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            recent_messages, corrections, proficiency_level
        )
        
        return StructuredFeedback(
            conversation_continuation=continuation,
            grammar_feedback=grammar_feedback,
            error_corrections=detailed_corrections,
            alternative_expressions=alternatives,
            native_translation=native_translation,
            message_count=len(recent_messages),
            overall_assessment=overall_assessment
        )
    
    def _generate_conversation_continuation(
        self,
        recent_messages: List[Message],
        proficiency_level: ProficiencyLevel,
        current_topic: Optional[str] = None
    ) -> str:
        """Generate conversation continuation suggestions.
        
        Args:
            recent_messages: Recent user messages
            proficiency_level: User's proficiency level
            current_topic: Current conversation topic
            
        Returns:
            Conversation continuation suggestion
        """
        if not recent_messages:
            return "Let's continue our conversation. What would you like to talk about next?"
        
        last_message = recent_messages[-1].content
        topic_context = f" about {current_topic}" if current_topic else ""
        
        # Generate level-appropriate continuation prompts
        if proficiency_level in [ProficiencyLevel.A1, ProficiencyLevel.A2]:
            continuations = [
                f"That's interesting! Can you tell me more{topic_context}?",
                f"I see. What do you think about that?",
                f"Good! Can you give me an example?",
                f"Nice! What else would you like to share{topic_context}?"
            ]
        elif proficiency_level == ProficiencyLevel.B1:
            continuations = [
                f"That's a thoughtful point{topic_context}. How do you feel about it?",
                f"Interesting perspective! What led you to think that way?",
                f"I understand. Could you elaborate on that idea?",
                f"That makes sense. What are your thoughts on the implications?"
            ]
        else:  # B2, C1, C2
            continuations = [
                f"That's a nuanced observation{topic_context}. What factors influenced your opinion?",
                f"Fascinating insight! How does this relate to your personal experience?",
                f"I appreciate your perspective. What counterarguments might exist?",
                f"Excellent analysis! What broader implications do you see?"
            ]
        
        # Simple selection based on message content
        import random
        return random.choice(continuations)
    
    def _create_detailed_corrections(
        self,
        corrections: List[Correction],
        proficiency_level: ProficiencyLevel
    ) -> List[DetailedCorrection]:
        """Convert basic corrections to detailed corrections with examples.
        
        Args:
            corrections: Basic corrections
            proficiency_level: User's proficiency level
            
        Returns:
            List of detailed corrections
        """
        detailed_corrections = []
        
        for correction in corrections[:3]:  # Limit to 3 corrections
            # Map basic category to extended category
            extended_category = self._map_to_extended_category(correction.category)
            
            # Generate examples based on the correction
            examples = self._generate_correction_examples(
                correction, proficiency_level
            )
            
            # Generate rule reference if applicable
            rule_reference = self._generate_rule_reference(correction, extended_category)
            
            detailed_correction = DetailedCorrection(
                original=correction.original,
                correction=correction.correction,
                explanation=correction.explanation,
                category=extended_category,
                examples=examples,
                rule_reference=rule_reference
            )
            
            detailed_corrections.append(detailed_correction)
        
        return detailed_corrections
    
    def _map_to_extended_category(self, basic_category: CorrectionCategory) -> ExtendedCorrectionCategory:
        """Map basic correction category to extended category.
        
        Args:
            basic_category: Basic correction category
            
        Returns:
            Extended correction category
        """
        mapping = {
            CorrectionCategory.GRAMMAR: ExtendedCorrectionCategory.GRAMMAR,
            CorrectionCategory.VOCABULARY: ExtendedCorrectionCategory.VOCABULARY,
            CorrectionCategory.PRONUNCIATION: ExtendedCorrectionCategory.PRONUNCIATION,
            CorrectionCategory.STYLE: ExtendedCorrectionCategory.STYLE
        }
        
        return mapping.get(basic_category, ExtendedCorrectionCategory.GRAMMAR)
    
    def _generate_correction_examples(
        self,
        correction: Correction,
        proficiency_level: ProficiencyLevel
    ) -> List[str]:
        """Generate examples for a correction.
        
        Args:
            correction: The correction to generate examples for
            proficiency_level: User's proficiency level
            
        Returns:
            List of example sentences
        """
        # This is a simplified implementation
        # In a real system, this would use AI or a comprehensive database
        
        examples = []
        
        if correction.category == CorrectionCategory.GRAMMAR:
            if "verb" in correction.explanation.lower():
                examples = [
                    f"Correct: {correction.correction}",
                    f"Also correct: I {correction.correction.split()[-1]} every day",
                    f"Remember: Use '{correction.correction.split()[-1]}' for present tense"
                ]
            elif "article" in correction.explanation.lower():
                examples = [
                    f"Correct: {correction.correction}",
                    f"The article is needed here",
                    f"Remember: Use 'the' for specific things"
                ]
            else:
                examples = [
                    f"Correct: {correction.correction}",
                    f"This follows standard grammar rules",
                    f"Practice this pattern more"
                ]
        elif correction.category == CorrectionCategory.VOCABULARY:
            examples = [
                f"Better word choice: {correction.correction}",
                f"This word fits the context better",
                f"Native speakers often use this word"
            ]
        else:
            examples = [
                f"Improved version: {correction.correction}",
                f"This sounds more natural",
                f"Good practice for fluency"
            ]
        
        return examples[:2]  # Limit to 2 examples
    
    def _generate_rule_reference(
        self,
        correction: Correction,
        category: ExtendedCorrectionCategory
    ) -> Optional[str]:
        """Generate grammar rule reference if applicable.
        
        Args:
            correction: The correction
            category: Extended correction category
            
        Returns:
            Rule reference or None
        """
        if category == ExtendedCorrectionCategory.GRAMMAR:
            if "verb" in correction.explanation.lower():
                return "Present tense verb conjugation"
            elif "article" in correction.explanation.lower():
                return "Definite article usage"
            elif "preposition" in correction.explanation.lower():
                return "Preposition selection"
            else:
                return "Basic grammar rules"
        
        return None
    
    def _generate_alternative_expressions(
        self,
        recent_messages: List[Message],
        proficiency_level: ProficiencyLevel,
        target_language: str
    ) -> List[AlternativeExpression]:
        """Generate alternative expressions for user messages.
        
        Args:
            recent_messages: Recent user messages
            proficiency_level: User's proficiency level
            target_language: Target language
            
        Returns:
            List of alternative expressions
        """
        alternatives = []
        
        # Analyze recent messages for expressions that could be improved
        for message in recent_messages[-2:]:  # Last 2 messages
            content = message.content.strip()
            if len(content) > 10:  # Only for substantial messages
                # Generate simple alternatives (in real implementation, use AI)
                alternative = self._create_alternative_expression(
                    content, proficiency_level, target_language
                )
                if alternative:
                    alternatives.append(alternative)
        
        return alternatives[:2]  # Limit to 2 alternatives
    
    def _create_alternative_expression(
        self,
        original: str,
        proficiency_level: ProficiencyLevel,
        target_language: str
    ) -> Optional[AlternativeExpression]:
        """Create an alternative expression for a given text.
        
        Args:
            original: Original text
            proficiency_level: User's proficiency level
            target_language: Target language
            
        Returns:
            Alternative expression or None
        """
        # Simplified implementation - in reality, use AI for this
        
        # Common patterns to suggest alternatives for
        if "I think" in original:
            # Map proficiency levels to numeric values for comparison
            level_values = {
                "A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6,
                "beginner": 1, "intermediate": 3, "advanced": 5, "native": 6
            }
            level_num = level_values.get(str(proficiency_level), 3)
            
            return AlternativeExpression(
                original="I think",
                alternative="In my opinion" if level_num >= 3 else "I believe",
                context="Expressing opinions",
                formality_level="neutral",
                usage_note="More formal way to express your thoughts"
            )
        elif "very good" in original.lower():
            level_values = {
                "A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6,
                "beginner": 1, "intermediate": 3, "advanced": 5, "native": 6
            }
            level_num = level_values.get(str(proficiency_level), 3)
            
            return AlternativeExpression(
                original="very good",
                alternative="excellent" if level_num >= 2 else "really good",
                context="Describing quality",
                formality_level="neutral",
                usage_note="More precise and natural expression"
            )
        elif "a lot of" in original.lower():
            return AlternativeExpression(
                original="a lot of",
                alternative="many" if "people" in original or "things" in original else "much",
                context="Expressing quantity",
                formality_level="neutral",
                usage_note="More precise quantifier"
            )
        
        return None
    
    def _generate_grammar_feedback(
        self,
        corrections: List[Correction],
        proficiency_level: ProficiencyLevel,
        target_language: str
    ) -> Optional[GrammarFeedback]:
        """Generate grammar-specific feedback if applicable.
        
        Args:
            corrections: Available corrections
            proficiency_level: User's proficiency level
            target_language: Target language
            
        Returns:
            Grammar feedback or None
        """
        # Find the most significant grammar correction
        grammar_corrections = [
            c for c in corrections 
            if c.category == CorrectionCategory.GRAMMAR
        ]
        
        if not grammar_corrections:
            return None
        
        # Take the first grammar correction for detailed feedback
        correction = grammar_corrections[0]
        
        # Generate grammar rule explanation
        rule_name, explanation, correct_usage, incorrect_usage, examples = self._analyze_grammar_pattern(
            correction, proficiency_level
        )
        
        difficulty_level = self._determine_difficulty_level(proficiency_level)
        
        return GrammarFeedback(
            rule_name=rule_name,
            explanation=explanation,
            correct_usage=correct_usage,
            incorrect_usage=incorrect_usage,
            additional_examples=examples,
            difficulty_level=difficulty_level
        )
    
    def _analyze_grammar_pattern(
        self,
        correction: Correction,
        proficiency_level: ProficiencyLevel
    ) -> Tuple[str, str, str, str, List[str]]:
        """Analyze grammar pattern and generate detailed feedback.
        
        Args:
            correction: Grammar correction
            proficiency_level: User's proficiency level
            
        Returns:
            Tuple of (rule_name, explanation, correct_usage, incorrect_usage, examples)
        """
        # Simplified pattern analysis
        original = correction.original.lower()
        corrected = correction.correction.lower()
        
        if "verb" in correction.explanation.lower():
            return (
                "Verb Tense Agreement",
                "Verbs must agree with their subjects and use correct tense",
                correction.correction,
                correction.original,
                ["I go to school", "She goes to school", "They went yesterday"]
            )
        elif "article" in correction.explanation.lower():
            return (
                "Article Usage",
                "Use 'the' for specific items, 'a/an' for general items",
                correction.correction,
                correction.original,
                ["The book on the table", "A book is useful", "An apple a day"]
            )
        elif "preposition" in correction.explanation.lower():
            return (
                "Preposition Selection",
                "Different verbs and contexts require specific prepositions",
                correction.correction,
                correction.original,
                ["Listen to music", "Look at the picture", "Think about it"]
            )
        else:
            return (
                "Grammar Rule",
                correction.explanation,
                correction.correction,
                correction.original,
                ["Practice makes perfect", "Keep studying!", "You're improving!"]
            )
    
    def _determine_difficulty_level(self, proficiency_level: ProficiencyLevel) -> str:
        """Determine difficulty level based on proficiency.
        
        Args:
            proficiency_level: User's proficiency level
            
        Returns:
            Difficulty level string
        """
        if proficiency_level in [ProficiencyLevel.A1, ProficiencyLevel.A2]:
            return "beginner"
        elif proficiency_level in [ProficiencyLevel.B1, ProficiencyLevel.B2]:
            return "intermediate"
        else:
            return "advanced"
    
    async def _generate_native_translation(
        self,
        recent_messages: List[Message],
        native_language: str,
        target_language: str
    ) -> Optional[str]:
        """Generate native language translation if user wrote in native language.
        
        Args:
            recent_messages: Recent user messages
            native_language: User's native language
            target_language: Target language
            
        Returns:
            Translation or None
        """
        # Import here to avoid circular imports
        try:
            from src.application.services.translation_service_interface import TranslationServiceInterface
            
            # Check if translation service is available
            translation_service = getattr(self, '_translation_service', None)
            if not isinstance(translation_service, TranslationServiceInterface):
                # Fallback to simple heuristic if no translation service
                return self._simple_native_translation_fallback(
                    recent_messages, native_language, target_language
                )
            
            # Check recent messages for native language content
            for message in recent_messages:
                content = message.content.strip()
                if not content:
                    continue
                
                # Use translation service to detect if message is in native language
                is_native = await translation_service.is_native_language_text(
                    content, native_language.lower(), target_language.lower()
                )
                
                if is_native:
                    # Translate to target language
                    translation_result = await translation_service.translate_text(
                        content, 
                        native_language.lower(), 
                        target_language.lower()
                    )
                    
                    if translation_result.quality.value in ['high', 'medium']:
                        target_lang_name = self._get_language_name(target_language)
                        return f"{target_lang_name} translation: {translation_result.translated_text}"
            
            return None
            
        except Exception as e:
            logger.warning(f"Translation service failed, using fallback: {e}")
            return self._simple_native_translation_fallback(
                recent_messages, native_language, target_language
            )
    
    def _simple_native_translation_fallback(
        self,
        recent_messages: List[Message],
        native_language: str,
        target_language: str
    ) -> Optional[str]:
        """Fallback method for native translation when service is unavailable.
        
        Args:
            recent_messages: Recent user messages
            native_language: User's native language
            target_language: Target language
            
        Returns:
            Simple translation indication or None
        """
        for message in recent_messages:
            content = message.content.strip()
            
            # Simple heuristic: if message contains language-specific characters or words
            if native_language.upper() == "TR" and target_language.upper() == "EN":
                turkish_indicators = ["ğ", "ş", "ç", "ı", "ö", "ü", "ve", "bir", "bu", "şu", "o"]
                if any(indicator in content.lower() for indicator in turkish_indicators):
                    return f"English translation: [Translation service unavailable]"
            elif native_language.upper() == "ES" and target_language.upper() == "EN":
                spanish_indicators = ["ñ", "¿", "¡", "que", "con", "por", "para", "una", "uno"]
                if any(indicator in content.lower() for indicator in spanish_indicators):
                    return f"English translation: [Translation service unavailable]"
            # Add more language pairs as needed
        
        return None
    
    def _get_language_name(self, language_code: str) -> str:
        """Get human-readable language name from code.
        
        Args:
            language_code: Language code (e.g., 'en', 'tr')
            
        Returns:
            Language name
        """
        language_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'tr': 'Turkish', 'ar': 'Arabic',
            'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ru': 'Russian'
        }
        return language_names.get(language_code.lower(), language_code.upper())
    
    def _generate_overall_assessment(
        self,
        recent_messages: List[Message],
        corrections: List[Correction],
        proficiency_level: ProficiencyLevel
    ) -> str:
        """Generate overall assessment of user's performance.
        
        Args:
            recent_messages: Recent user messages
            corrections: Available corrections
            proficiency_level: User's proficiency level
            
        Returns:
            Overall assessment string
        """
        message_count = len(recent_messages)
        correction_count = len(corrections)
        
        if correction_count == 0:
            assessments = [
                "Excellent work! Your messages were clear and well-structured.",
                "Great job! No major corrections needed in your recent messages.",
                "Well done! You're communicating effectively."
            ]
        elif correction_count <= 2:
            assessments = [
                "Good progress! Just a few small improvements to work on.",
                "Nice work! You're making steady improvements.",
                "Keep it up! Your language skills are developing well."
            ]
        else:
            assessments = [
                "You're learning! Focus on the corrections to improve further.",
                "Good effort! Practice the highlighted areas for better fluency.",
                "Keep practicing! Each correction helps you improve."
            ]
        
        # Add proficiency-specific encouragement
        if proficiency_level in [ProficiencyLevel.A1, ProficiencyLevel.A2]:
            assessments = [f"{assessment} Remember, every mistake is a learning opportunity!" for assessment in assessments]
        elif proficiency_level == ProficiencyLevel.B1:
            assessments = [f"{assessment} You're building confidence in your communication." for assessment in assessments]
        
        import random
        return random.choice(assessments)


class PedagogyEngine:
    """Main pedagogy engine for educational response optimization."""
    
    def __init__(self, constraints: PedagogicalConstraints = None):
        """Initialize pedagogy engine.
        
        Args:
            constraints: Pedagogical constraints configuration
        """
        self.constraints = constraints or PedagogicalConstraints()
        self.response_formatter = ResponseFormatter(self.constraints)
        self.correction_selector = CorrectionSelector(self.constraints)
        self.exercise_generator = MicroExerciseGenerator(self.constraints)
        self.structured_feedback_generator = StructuredFeedbackGenerator(self.constraints)
        
        # Statistics tracking
        self.total_responses_processed = 0
        self.total_corrections_selected = 0
        self.total_exercises_generated = 0
        self.total_structured_feedback_generated = 0
    
    def process_response(
        self,
        raw_response: str,
        all_corrections: List[Correction],
        conversation_context: ConversationContext,
        message_count: int = 0,
        last_exercise_message: Optional[int] = None
    ) -> PedagogicalResponse:
        """Process AI response with pedagogical optimization.
        
        Args:
            raw_response: Raw AI response
            all_corrections: All available corrections
            conversation_context: Current conversation context
            message_count: Current message count in session
            last_exercise_message: Message number of last exercise
            
        Returns:
            Pedagogically optimized response
        """
        self.total_responses_processed += 1
        
        proficiency_level = conversation_context.user_preferences.proficiency_level
        
        # Format response according to constraints
        formatted_response = self.response_formatter.format_response(
            raw_response, proficiency_level
        )
        
        # Select most valuable corrections
        recent_corrections = self._get_recent_corrections(conversation_context)
        selected_corrections = self.correction_selector.select_corrections(
            all_corrections, proficiency_level, recent_corrections
        )
        self.total_corrections_selected += len(selected_corrections)
        
        # Generate micro-exercise if appropriate
        micro_exercise = None
        if (conversation_context.session_mode == SessionMode.TUTOR and
            self.exercise_generator.should_generate_exercise(
                message_count, selected_corrections, last_exercise_message
            )):
            
            exercise_prompt = self.exercise_generator.generate_exercise_prompt(
                selected_corrections, proficiency_level
            )
            if exercise_prompt:
                micro_exercise = exercise_prompt
                self.total_exercises_generated += 1
        
        # Create response metadata
        metadata = {
            'original_sentence_count': len(self.response_formatter._split_into_sentences(raw_response)),
            'formatted_sentence_count': len(self.response_formatter._split_into_sentences(formatted_response)),
            'total_corrections_available': len(all_corrections),
            'corrections_selected': len(selected_corrections),
            'exercise_generated': micro_exercise is not None,
            'proficiency_level': str(proficiency_level),
            'processing_timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Processed response: {len(selected_corrections)} corrections, exercise: {micro_exercise is not None}")
        
        return PedagogicalResponse(
            formatted_response=formatted_response,
            selected_corrections=selected_corrections,
            micro_exercise=micro_exercise,
            response_metadata=metadata
        )
    
    def generate_structured_feedback(
        self,
        recent_messages: List[Message],
        all_corrections: List[Correction],
        conversation_context: ConversationContext,
        message_count: int,
        last_feedback_message: Optional[int] = None,
        current_topic: Optional[str] = None
    ) -> Optional[StructuredFeedback]:
        """Generate structured feedback for 3-message cycles.
        
        Args:
            recent_messages: Recent user messages (should be last 3)
            all_corrections: All available corrections from the messages
            conversation_context: Current conversation context
            message_count: Current message count in session
            last_feedback_message: Message number of last structured feedback
            current_topic: Current conversation topic
            
        Returns:
            Structured feedback if conditions are met, None otherwise
        """
        # Check if structured feedback should be provided
        if not self.structured_feedback_generator.should_provide_structured_feedback(
            message_count, last_feedback_message
        ):
            return None
        
        # Ensure we have enough messages
        if len(recent_messages) < 3:
            logger.warning(f"Not enough messages for structured feedback: {len(recent_messages)}")
            return None
        
        # Take only the last 3 user messages
        last_three_messages = recent_messages[-3:]
        
        # Filter corrections to only those from the last 3 messages
        relevant_corrections = self._filter_corrections_for_messages(
            all_corrections, last_three_messages
        )
        
        proficiency_level = conversation_context.user_preferences.proficiency_level
        
        # Extract language preferences
        native_language = getattr(conversation_context.user_preferences, 'native_language', 'TR')
        target_language = getattr(conversation_context.user_preferences, 'target_language', 'EN')
        
        try:
            structured_feedback = self.structured_feedback_generator.generate_structured_feedback(
                recent_messages=last_three_messages,
                corrections=relevant_corrections,
                proficiency_level=proficiency_level,
                native_language=native_language,
                target_language=target_language,
                current_topic=current_topic
            )
            
            self.total_structured_feedback_generated += 1
            logger.info(f"Generated structured feedback for {len(last_three_messages)} messages with {len(relevant_corrections)} corrections")
            
            return structured_feedback
            
        except Exception as e:
            logger.error(f"Failed to generate structured feedback: {e}")
            return None
    
    def _filter_corrections_for_messages(
        self,
        all_corrections: List[Correction],
        target_messages: List[Message]
    ) -> List[Correction]:
        """Filter corrections to only those relevant to specific messages.
        
        Args:
            all_corrections: All available corrections
            target_messages: Messages to filter corrections for
            
        Returns:
            Filtered corrections
        """
        # In a real implementation, corrections would have message IDs
        # For now, return all corrections as they're assumed to be from recent messages
        return all_corrections
    
    def _get_recent_corrections(self, conversation_context: ConversationContext) -> List[Correction]:
        """Extract recent corrections from conversation context.
        
        Args:
            conversation_context: Current conversation context
            
        Returns:
            List of recent corrections
        """
        recent_corrections = []
        
        # Extract corrections from recent messages
        for message in conversation_context.recent_messages[-10:]:  # Last 10 messages
            if message.corrections:
                recent_corrections.extend(message.corrections)
        
        return recent_corrections
    
    def get_engine_stats(self) -> Dict[str, any]:
        """Get pedagogy engine statistics.
        
        Returns:
            Dictionary with engine statistics
        """
        avg_corrections = (self.total_corrections_selected / self.total_responses_processed 
                          if self.total_responses_processed > 0 else 0)
        
        exercise_rate = (self.total_exercises_generated / self.total_responses_processed * 100
                        if self.total_responses_processed > 0 else 0)
        
        structured_feedback_rate = (self.total_structured_feedback_generated / self.total_responses_processed * 100
                                   if self.total_responses_processed > 0 else 0)
        
        return {
            'total_responses_processed': self.total_responses_processed,
            'total_corrections_selected': self.total_corrections_selected,
            'total_exercises_generated': self.total_exercises_generated,
            'total_structured_feedback_generated': self.total_structured_feedback_generated,
            'average_corrections_per_response': round(avg_corrections, 2),
            'exercise_generation_rate_percent': round(exercise_rate, 2),
            'structured_feedback_rate_percent': round(structured_feedback_rate, 2),
            'constraints': {
                'min_sentences': self.constraints.min_response_sentences,
                'max_sentences': self.constraints.max_response_sentences,
                'max_corrections': self.constraints.max_corrections_per_message,
                'exercise_frequency': self.constraints.micro_exercise_frequency
            }
        }
    
    def update_constraints(self, new_constraints: PedagogicalConstraints):
        """Update pedagogical constraints.
        
        Args:
            new_constraints: New constraints configuration
        """
        self.constraints = new_constraints
        self.response_formatter = ResponseFormatter(self.constraints)
        self.correction_selector = CorrectionSelector(self.constraints)
        self.exercise_generator = MicroExerciseGenerator(self.constraints)
        
        logger.info("Updated pedagogical constraints")
    
    async def optimize_response(
        self,
        ai_response: str,
        corrections: List[Correction],
        conversation_context: ConversationContext,
        session_message_count: int
    ) -> PedagogicalResponse:
        """Basic response optimization."""
        return PedagogicalResponse(
            formatted_response=ai_response,
            selected_corrections=corrections[:self.constraints.max_corrections_per_message],
            micro_exercise=None,
            response_metadata={}
        )
    
    async def optimize_response_with_feedback(
        self,
        ai_response: str,
        corrections: List[Correction],
        conversation_context: ConversationContext,
        session_message_count: int,
        structured_feedback: Optional[StructuredFeedback] = None
    ) -> PedagogicalResponse:
        """Optimize response with enhanced feedback integration.
        
        Args:
            ai_response: AI response to optimize
            corrections: List of corrections
            conversation_context: Conversation context
            session_message_count: Current message count
            structured_feedback: Optional structured feedback
            
        Returns:
            Enhanced pedagogical response
        """
        try:
            # Use existing optimize_response method as base
            base_response = await self.optimize_response(
                ai_response, corrections, conversation_context, session_message_count
            )
            
            # If structured feedback is provided, integrate it into the response
            if structured_feedback:
                # Append structured feedback to the response
                enhanced_response = base_response.formatted_response
                
                # Add conversation continuation if available
                if structured_feedback.conversation_continuation:
                    enhanced_response += f"\n\n{structured_feedback.conversation_continuation}"
                
                # Add overall assessment
                if structured_feedback.overall_assessment:
                    enhanced_response += f"\n\n{structured_feedback.overall_assessment}"
                
                # Update metadata
                enhanced_metadata = base_response.response_metadata.copy()
                enhanced_metadata.update({
                    'structured_feedback_provided': True,
                    'feedback_message_count': structured_feedback.message_count,
                    'has_grammar_feedback': structured_feedback.has_grammar_feedback(),
                    'corrections_count': len(structured_feedback.error_corrections),
                    'alternatives_count': len(structured_feedback.alternative_expressions)
                })
                
                return PedagogicalResponse(
                    formatted_response=enhanced_response,
                    selected_corrections=base_response.selected_corrections,
                    micro_exercise=base_response.micro_exercise,
                    response_metadata=enhanced_metadata
                )
            
            # Return base response if no structured feedback
            return base_response
            
        except Exception as e:
            logger.error(f"Enhanced response optimization failed: {e}")
            # Fall back to basic optimization
            return await self.optimize_response(
                ai_response, corrections, conversation_context, session_message_count
            )