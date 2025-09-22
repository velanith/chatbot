"""AI Prompt Service for generating specialized prompts for language learning features."""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.domain.entities.session import ProficiencyLevel
from src.domain.entities.message import Message, Correction
from src.domain.entities.topic import Topic, TopicCategory
from src.domain.entities.assessment import AssessmentQuestion, AssessmentResponse, LanguagePair


logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of AI prompts supported."""
    LEVEL_ASSESSMENT_EVALUATION = "level_assessment_evaluation"
    LEVEL_ASSESSMENT_QUESTION = "level_assessment_question"
    TOPIC_SUGGESTION = "topic_suggestion"
    TOPIC_STARTER = "topic_starter"
    TOPIC_COHERENCE_CHECK = "topic_coherence_check"
    STRUCTURED_FEEDBACK = "structured_feedback"
    ENHANCED_TRANSLATION = "enhanced_translation"
    TRANSLATION_QUALITY = "translation_quality"


@dataclass
class PromptContext:
    """Context information for prompt generation."""
    proficiency_level: ProficiencyLevel
    language_pair: LanguagePair
    user_preferences: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Message]] = None
    current_topic: Optional[Topic] = None
    additional_context: Optional[Dict[str, Any]] = None


class AIPromptService:
    """Service for generating AI prompts for language learning features."""
    
    def __init__(self):
        """Initialize the AI prompt service."""
        self.language_names = {
            'EN': 'English', 'ES': 'Spanish', 'FR': 'French', 'DE': 'German',
            'IT': 'Italian', 'PT': 'Portuguese', 'TR': 'Turkish', 'AR': 'Arabic',
            'ZH': 'Chinese', 'JA': 'Japanese', 'KO': 'Korean', 'RU': 'Russian'
        }
        self.prompt_version = "v1.0"
    
    def generate_level_assessment_evaluation_prompt(
        self,
        question: AssessmentQuestion,
        user_response: str,
        language_pair: LanguagePair,
        previous_responses: Optional[List[AssessmentResponse]] = None
    ) -> str:
        """Generate prompt for evaluating user responses in level assessment.
        
        Args:
            question: Assessment question that was asked
            user_response: User's response to evaluate
            language_pair: Native and target language pair
            previous_responses: Previous assessment responses for context
            
        Returns:
            Evaluation prompt for AI
        """
        target_lang = language_pair.target_language.upper()
        native_lang = language_pair.native_language.upper()
        
        target_lang_name = self.language_names.get(target_lang, 'the target language')
        native_lang_name = self.language_names.get(native_lang, 'the native language')
        
        # Build context from previous responses
        context = ""
        if previous_responses:
            avg_scores = {
                'complexity': sum(r.complexity_score for r in previous_responses) / len(previous_responses),
                'accuracy': sum(r.accuracy_score for r in previous_responses) / len(previous_responses),
                'fluency': sum(r.fluency_score for r in previous_responses) / len(previous_responses)
            }
            context = f"\nPrevious response averages: Complexity: {avg_scores['complexity']:.2f}, Accuracy: {avg_scores['accuracy']:.2f}, Fluency: {avg_scores['fluency']:.2f}"
        
        return f"""You are an expert language assessment evaluator for {target_lang_name} proficiency. 
You are evaluating a {native_lang_name} speaker's {target_lang_name} response to determine their proficiency level.

CEFR Levels:
- A1: Basic user, simple phrases, present tense, basic vocabulary
- A2: Elementary, simple sentences, past/future tense, everyday topics
- B1: Intermediate, connected speech, opinions, complex sentences
- B2: Upper-intermediate, detailed descriptions, abstract topics, nuanced expression
- C1: Advanced, fluent expression, complex ideas, sophisticated vocabulary
- C2: Proficient, native-like fluency, subtle meanings, complex argumentation

Evaluate the response on three dimensions (0.0-1.0 scale):

1. COMPLEXITY: Sentence structure, grammar complexity, vocabulary sophistication
   - 0.0-0.3: Simple words, basic sentences, elementary grammar
   - 0.4-0.6: Some complex sentences, intermediate vocabulary
   - 0.7-1.0: Complex structures, advanced vocabulary, sophisticated expression

2. ACCURACY: Grammar correctness, word choice, language mechanics
   - 0.0-0.3: Many errors that impede understanding
   - 0.4-0.6: Some errors but meaning is clear
   - 0.7-1.0: Few or no errors, natural language use

3. FLUENCY: Natural flow, coherence, completeness of response
   - 0.0-0.3: Fragmented, incomplete thoughts
   - 0.4-0.6: Understandable but some hesitation/awkwardness
   - 0.7-1.0: Natural, coherent, complete expression

Expected level for this question: {question.expected_level}
Question category: {question.category}{context}

Respond in this EXACT format:
COMPLEXITY_SCORE: [0.0-1.0]
ACCURACY_SCORE: [0.0-1.0]
FLUENCY_SCORE: [0.0-1.0]
ESTIMATED_LEVEL: [A1/A2/B1/B2/C1/C2]
FEEDBACK: [Brief explanation of the assessment]"""
    
    def generate_level_assessment_question_prompt(
        self,
        target_level: ProficiencyLevel,
        language_pair: LanguagePair,
        question_count: int,
        previous_questions: Optional[List[AssessmentQuestion]] = None
    ) -> str:
        """Generate prompt for creating assessment questions.
        
        Args:
            target_level: Target proficiency level to assess
            language_pair: Native and target language pair
            question_count: Number of questions to generate
            previous_questions: Previously asked questions to avoid repetition
            
        Returns:
            Question generation prompt for AI
        """
        target_lang_name = self.language_names.get(language_pair.target_language.upper(), 'the target language')
        native_lang_name = self.language_names.get(language_pair.native_language.upper(), 'the native language')
        
        # Build context about previous questions
        previous_context = ""
        if previous_questions:
            topics = [q.category for q in previous_questions]
            previous_context = f"\nAvoid repeating these topics: {', '.join(set(topics))}"
        
        level_descriptions = {
            ProficiencyLevel.A1: "Basic level - simple present tense, basic vocabulary, personal information",
            ProficiencyLevel.A2: "Elementary level - past/future tense, everyday situations, simple descriptions",
            ProficiencyLevel.B1: "Intermediate level - opinions, experiences, plans, connected speech",
            ProficiencyLevel.B2: "Upper-intermediate level - abstract topics, detailed descriptions, arguments",
            ProficiencyLevel.C1: "Advanced level - complex ideas, nuanced expression, sophisticated vocabulary",
            ProficiencyLevel.C2: "Proficient level - subtle meanings, complex argumentation, native-like fluency"
        }
        
        return f"""You are creating {target_lang_name} proficiency assessment questions for {native_lang_name} speakers.

Target Level: {target_level} - {level_descriptions.get(target_level, 'Unknown level')}

Create {question_count} assessment question(s) that will help determine if a learner is at the {target_level} level.

Requirements:
- Questions should be appropriate for {target_level} level assessment
- Each question should elicit responses that demonstrate key {target_level} competencies
- Questions should be engaging and culturally appropriate
- Vary question types: open-ended, situational, opinion-based, descriptive
- Questions should encourage natural language use, not just grammar exercises{previous_context}

For each question, provide:
1. The question text in {target_lang_name}
2. Expected response characteristics for {target_level} level
3. Key grammar/vocabulary points being assessed
4. Suggested follow-up if response is unclear

Format each question as:
QUESTION: [question text]
EXPECTED_LEVEL: {target_level}
CATEGORY: [topic category]
ASSESSMENT_FOCUS: [what this question tests]
FOLLOW_UP: [optional follow-up question]

Generate {question_count} question(s) now:"""
    
    def generate_topic_suggestion_prompt(
        self,
        proficiency_level: ProficiencyLevel,
        language_pair: LanguagePair,
        user_interests: Optional[List[str]] = None,
        conversation_history: Optional[List[str]] = None,
        count: int = 5
    ) -> str:
        """Generate prompt for suggesting conversation topics.
        
        Args:
            proficiency_level: User's proficiency level
            language_pair: Native and target language pair
            user_interests: User's stated interests
            conversation_history: Recent conversation topics
            count: Number of topics to suggest
            
        Returns:
            Topic suggestion prompt for AI
        """
        target_lang_name = self.language_names.get(language_pair.target_language.upper(), 'the target language')
        
        # Build user context
        interests_context = ""
        if user_interests:
            interests_context = f"\nUser interests: {', '.join(user_interests)}"
        
        history_context = ""
        if conversation_history:
            history_context = f"\nRecent topics discussed: {', '.join(conversation_history[-5:])}"
        
        level_guidelines = {
            ProficiencyLevel.A1: "Simple, concrete topics about daily life, family, hobbies, basic needs",
            ProficiencyLevel.A2: "Everyday situations, past experiences, future plans, simple descriptions",
            ProficiencyLevel.B1: "Personal opinions, experiences, travel, work, current events (simplified)",
            ProficiencyLevel.B2: "Abstract concepts, detailed discussions, cultural topics, complex situations",
            ProficiencyLevel.C1: "Sophisticated topics, nuanced discussions, professional subjects, complex ideas",
            ProficiencyLevel.C2: "Any topic with subtle distinctions, complex argumentation, specialized subjects"
        }
        
        return f"""You are suggesting engaging conversation topics for a {proficiency_level.value} level {target_lang_name} learner.

Level Guidelines: {level_guidelines.get(proficiency_level, 'Unknown level')}

Requirements:
- Topics should be appropriate for {proficiency_level.value} level
- Topics should encourage natural conversation and language practice
- Consider cultural relevance and universal appeal
- Avoid sensitive or controversial topics unless appropriate for advanced levels
- Each topic should have clear conversation potential{interests_context}{history_context}

For each topic, provide:
1. Topic name (concise, engaging)
2. Brief description of what to discuss
3. 2-3 conversation starter questions
4. Key vocabulary/grammar this topic practices

Format each topic as:
TOPIC: [topic name]
DESCRIPTION: [what this topic covers]
DIFFICULTY: {proficiency_level.value}
CATEGORY: [general category like daily_life, culture, etc.]
STARTERS: [conversation starter questions]
LANGUAGE_FOCUS: [key language elements practiced]

Generate {count} engaging topics now:"""
    
    def generate_topic_starter_prompt(
        self,
        topic: Topic,
        proficiency_level: ProficiencyLevel,
        language_pair: LanguagePair,
        conversation_context: Optional[str] = None
    ) -> str:
        """Generate prompt for creating topic conversation starters.
        
        Args:
            topic: Topic to create starters for
            proficiency_level: User's proficiency level
            language_pair: Native and target language pair
            conversation_context: Optional context about the conversation
            
        Returns:
            Topic starter generation prompt for AI
        """
        target_lang_name = self.language_names.get(language_pair.target_language.upper(), 'the target language')
        
        context_info = ""
        if conversation_context:
            context_info = f"\nConversation context: {conversation_context}"
        
        return f"""You are starting a {target_lang_name} conversation about "{topic.name}" with a {proficiency_level.value} level learner.

Topic: {topic.name}
Description: {topic.description}
Category: {topic.category.value}
Difficulty Level: {topic.difficulty_level.value}{context_info}

Create an engaging conversation starter that:
- Introduces the topic naturally
- Is appropriate for {proficiency_level.value} level
- Encourages the learner to respond and share
- Uses vocabulary and grammar suitable for their level
- Is culturally appropriate and interesting
- Includes a clear question or prompt for response

The starter should be in {target_lang_name} and feel natural, not like a textbook exercise.

Generate a conversation starter now:"""
    
    def generate_topic_coherence_check_prompt(
        self,
        current_topic: Topic,
        recent_messages: List[Message],
        language_pair: LanguagePair
    ) -> str:
        """Generate prompt for checking topic coherence in conversation.
        
        Args:
            current_topic: Current conversation topic
            recent_messages: Recent messages in the conversation
            language_pair: Native and target language pair
            
        Returns:
            Topic coherence check prompt for AI
        """
        target_lang_name = self.language_names.get(language_pair.target_language.upper(), 'the target language')
        
        # Extract recent message content
        message_content = []
        for msg in recent_messages[-5:]:  # Last 5 messages
            role = "User" if msg.role.value == "user" else "Assistant"
            message_content.append(f"{role}: {msg.content}")
        
        conversation_text = "\n".join(message_content)
        
        return f"""You are analyzing conversation coherence for a {target_lang_name} learning session.

Current Topic: {current_topic.name}
Topic Description: {current_topic.description}
Topic Category: {current_topic.category}

Recent Conversation:
{conversation_text}

Analyze whether the conversation is still coherent with the current topic. Consider:
1. Are the messages still related to "{current_topic.name}"?
2. Has the conversation naturally evolved within the topic scope?
3. Has the conversation drifted to a completely different subject?
4. Would it be beneficial to suggest a topic transition?

Respond in this EXACT format:
COHERENT: [YES/NO]
CONFIDENCE: [0.0-1.0]
ANALYSIS: [Brief explanation of the coherence assessment]
SUGGESTION: [If not coherent, suggest what to do - continue, redirect, or transition]"""
    
    def generate_structured_feedback_prompt(
        self,
        recent_messages: List[Message],
        corrections: List[Correction],
        proficiency_level: ProficiencyLevel,
        language_pair: LanguagePair,
        current_topic: Optional[Topic] = None
    ) -> str:
        """Generate prompt for creating structured feedback.
        
        Args:
            recent_messages: Last 3 user messages for analysis
            corrections: Available corrections from the messages
            proficiency_level: User's proficiency level
            language_pair: Native and target language pair
            current_topic: Current conversation topic
            
        Returns:
            Structured feedback generation prompt for AI
        """
        target_lang_name = self.language_names.get(language_pair.target_language.upper(), 'the target language')
        native_lang_name = self.language_names.get(language_pair.native_language.upper(), 'the native language')
        
        # Extract user messages
        user_messages = [msg.content for msg in recent_messages if msg.role.value == "user"]
        messages_text = "\n".join([f"Message {i+1}: {msg}" for i, msg in enumerate(user_messages)])
        
        # Extract corrections
        corrections_text = ""
        if corrections:
            corrections_list = []
            for corr in corrections[:3]:  # Limit to 3 corrections
                corrections_list.append(f"- '{corr.original}' → '{corr.correction}' ({corr.explanation})")
            corrections_text = "\n".join(corrections_list)
        
        topic_context = ""
        if current_topic:
            topic_context = f"\nCurrent topic: {current_topic.name} - {current_topic.description}"
        
        return f"""You are providing structured feedback to a {proficiency_level.value} level {target_lang_name} learner.

User's recent messages:
{messages_text}

Identified corrections:
{corrections_text}{topic_context}

Create comprehensive structured feedback that includes:

1. CONVERSATION_CONTINUATION: A natural response that continues the conversation while incorporating the topic. This should be in {target_lang_name} and feel like a natural conversation partner response.

2. GRAMMAR_FEEDBACK: If there are grammar corrections, explain the most important grammar rule with:
   - Rule name and explanation
   - Correct vs incorrect usage examples
   - 2-3 additional practice examples

3. ERROR_CORRECTIONS: For each correction, provide:
   - Original text and correction
   - Clear explanation of why it's wrong
   - Category (grammar/vocabulary/style)
   - Alternative ways to express the same idea

4. ALTERNATIVE_EXPRESSIONS: Suggest 2-3 alternative ways to express ideas from their messages, showing:
   - Original expression
   - Alternative expression
   - Context for when to use each
   - Formality level differences

5. OVERALL_ASSESSMENT: Brief encouraging assessment of their progress and areas to focus on.

Format your response as:
CONVERSATION_CONTINUATION: [natural conversation response in {target_lang_name}]
GRAMMAR_FEEDBACK: [grammar explanation if applicable]
ERROR_CORRECTIONS: [detailed corrections with explanations]
ALTERNATIVE_EXPRESSIONS: [alternative ways to express ideas]
OVERALL_ASSESSMENT: [encouraging progress assessment]

Provide structured feedback now:"""
    
    def generate_enhanced_translation_prompt(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None,
        conversation_topic: Optional[str] = None,
        user_level: Optional[ProficiencyLevel] = None
    ) -> str:
        """Generate prompt for enhanced translation with context.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            context: Optional context for better translation
            conversation_topic: Current conversation topic
            user_level: User's proficiency level for appropriate complexity
            
        Returns:
            Enhanced translation prompt for AI
        """
        source_lang_name = self.language_names.get(source_language.upper(), source_language)
        target_lang_name = self.language_names.get(target_language.upper(), target_language)
        
        context_info = ""
        if context:
            context_info = f"\nContext: {context}"
        
        topic_info = ""
        if conversation_topic:
            topic_info = f"\nConversation topic: {conversation_topic}"
        
        level_info = ""
        if user_level:
            level_info = f"\nUser level: {user_level.value} - adjust complexity accordingly"
        
        return f"""You are providing an enhanced translation from {source_lang_name} to {target_lang_name}.

Text to translate: "{text}"{context_info}{topic_info}{level_info}

Provide a high-quality translation that:
- Maintains the original meaning and intent
- Uses natural, fluent {target_lang_name}
- Considers the context and conversation topic
- Is appropriate for the user's proficiency level
- Preserves the tone and style of the original

IMPORTANT: Provide ONLY the translation, no explanations or additional text.

Translation:"""
    
    def generate_translation_quality_assessment_prompt(
        self,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """Generate prompt for assessing translation quality.
        
        Args:
            original_text: Original text
            translated_text: Translated text to assess
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Translation quality assessment prompt for AI
        """
        source_lang_name = self.language_names.get(source_language.upper(), source_language)
        target_lang_name = self.language_names.get(target_language.upper(), target_language)
        
        return f"""You are assessing the quality of a translation from {source_lang_name} to {target_lang_name}.

Original ({source_lang_name}): "{original_text}"
Translation ({target_lang_name}): "{translated_text}"

Evaluate the translation quality considering:
1. Accuracy of meaning - Does it convey the same message?
2. Grammar correctness - Is the {target_lang_name} grammatically correct?
3. Natural fluency - Does it sound natural to native speakers?
4. Context appropriateness - Is it suitable for the context?
5. Completeness - Is all information preserved?

Rate the overall quality on a scale of 0.0 to 1.0 where:
- 0.0-0.3: Poor quality, significant errors or meaning loss
- 0.4-0.6: Acceptable quality, some issues but understandable
- 0.7-0.9: Good quality, minor issues, natural sounding
- 0.9-1.0: Excellent quality, native-like, perfect meaning preservation

Respond with ONLY a number between 0.0 and 1.0:"""
    
    def get_prompt_metadata(self, prompt_type: PromptType) -> Dict[str, Any]:
        """Get metadata about a specific prompt type.
        
        Args:
            prompt_type: Type of prompt to get metadata for
            
        Returns:
            Dictionary with prompt metadata
        """
        metadata = {
            PromptType.LEVEL_ASSESSMENT_EVALUATION: {
                "description": "Evaluates user responses in level assessment",
                "input_requirements": ["question", "user_response", "language_pair"],
                "output_format": "structured_scores_and_feedback",
                "temperature": 0.1,
                "max_tokens": 500
            },
            PromptType.LEVEL_ASSESSMENT_QUESTION: {
                "description": "Generates assessment questions for proficiency testing",
                "input_requirements": ["target_level", "language_pair"],
                "output_format": "structured_questions",
                "temperature": 0.7,
                "max_tokens": 800
            },
            PromptType.TOPIC_SUGGESTION: {
                "description": "Suggests conversation topics based on user preferences",
                "input_requirements": ["proficiency_level", "language_pair"],
                "output_format": "structured_topics",
                "temperature": 0.8,
                "max_tokens": 1000
            },
            PromptType.TOPIC_STARTER: {
                "description": "Creates conversation starters for specific topics",
                "input_requirements": ["topic", "proficiency_level", "language_pair"],
                "output_format": "conversation_starter",
                "temperature": 0.7,
                "max_tokens": 300
            },
            PromptType.TOPIC_COHERENCE_CHECK: {
                "description": "Checks if conversation stays on topic",
                "input_requirements": ["current_topic", "recent_messages"],
                "output_format": "coherence_analysis",
                "temperature": 0.3,
                "max_tokens": 400
            },
            PromptType.STRUCTURED_FEEDBACK: {
                "description": "Generates comprehensive feedback for 3-message cycles",
                "input_requirements": ["recent_messages", "corrections", "proficiency_level"],
                "output_format": "structured_feedback",
                "temperature": 0.6,
                "max_tokens": 1200
            },
            PromptType.ENHANCED_TRANSLATION: {
                "description": "Provides context-aware translations",
                "input_requirements": ["text", "source_language", "target_language"],
                "output_format": "translation_only",
                "temperature": 0.3,
                "max_tokens": 500
            },
            PromptType.TRANSLATION_QUALITY: {
                "description": "Assesses translation quality",
                "input_requirements": ["original_text", "translated_text", "languages"],
                "output_format": "quality_score",
                "temperature": 0.2,
                "max_tokens": 100
            }
        }
        
        return metadata.get(prompt_type, {})
    
    def validate_prompt_inputs(
        self,
        prompt_type: PromptType,
        **kwargs
    ) -> bool:
        """Validate that required inputs are provided for a prompt type.
        
        Args:
            prompt_type: Type of prompt to validate
            **kwargs: Input parameters to validate
            
        Returns:
            True if all required inputs are provided
        """
        metadata = self.get_prompt_metadata(prompt_type)
        required_inputs = metadata.get("input_requirements", [])
        
        for required_input in required_inputs:
            if required_input not in kwargs or kwargs[required_input] is None:
                logger.warning(f"Missing required input '{required_input}' for prompt type {prompt_type}")
                return False
        
        return True
    
    def get_recommended_llm_settings(self, prompt_type: PromptType) -> Dict[str, Any]:
        """Get recommended LLM settings for a prompt type.
        
        Args:
            prompt_type: Type of prompt to get settings for
            
        Returns:
            Dictionary with recommended LLM settings
        """
        metadata = self.get_prompt_metadata(prompt_type)
        
        return {
            "temperature": metadata.get("temperature", 0.7),
            "max_tokens": metadata.get("max_tokens", 500),
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "prompt_version": self.prompt_version
        }