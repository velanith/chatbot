"""Topic management service with AI-powered topic suggestion and management."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.entities.topic import Topic, TopicCategory
from src.domain.entities.language_preferences import LanguagePreferences
from src.domain.entities.session import ProficiencyLevel
from src.domain.entities.message import Message
from src.domain.repositories.topic_repository_interface import TopicRepositoryInterface
from src.application.services.llm_service_interface import (
    LLMServiceInterface, 
    LLMRequest, 
    LLMModel,
    LLMServiceError
)


logger = logging.getLogger(__name__)


class TopicManagerError(Exception):
    """Base exception for topic manager errors."""
    pass


class TopicSuggestionError(TopicManagerError):
    """Raised when topic suggestion fails."""
    pass


class TopicCoherenceError(TopicManagerError):
    """Raised when topic coherence checking fails."""
    pass


class TopicTransitionError(TopicManagerError):
    """Raised when topic transition detection fails."""
    pass


class TopicManager:
    """Service for AI-powered topic management and conversation guidance."""
    
    def __init__(
        self,
        topic_repository: TopicRepositoryInterface,
        llm_service: LLMServiceInterface,
        default_model: LLMModel = LLMModel.GPT_3_5_TURBO
    ):
        """Initialize topic manager.
        
        Args:
            topic_repository: Repository for topic data operations
            llm_service: LLM service for AI-powered functionality
            default_model: Default LLM model to use
        """
        self.topic_repository = topic_repository
        self.llm_service = llm_service
        self.default_model = default_model
        self._coherence_threshold = 0.7  # Minimum coherence score
        self._transition_keywords = [
            "let's talk about", "speaking of", "that reminds me", 
            "by the way", "on another note", "changing topics"
        ]
    
    async def suggest_topics(
        self, 
        user_preferences: LanguagePreferences, 
        limit: int = 5,
        exclude_recent: Optional[List[str]] = None
    ) -> List[Topic]:
        """Suggest relevant topics based on user preferences and AI analysis.
        
        Args:
            user_preferences: User's language learning preferences
            limit: Maximum number of topics to suggest
            exclude_recent: List of recently used topic IDs to exclude
            
        Returns:
            List of suggested topics
            
        Raises:
            TopicSuggestionError: If topic suggestion fails
        """
        try:
            logger.info(f"Suggesting topics for user {user_preferences.user_id}")
            
            # Get base topics from repository based on preferences
            base_topics = await self._get_base_topics(user_preferences, limit * 2)
            
            # Filter out recently used topics
            if exclude_recent:
                base_topics = [t for t in base_topics if t.id not in exclude_recent]
            
            # Use AI to rank and personalize topic suggestions
            suggested_topics = await self._ai_rank_topics(
                base_topics, user_preferences, limit
            )
            
            logger.info(f"Successfully suggested {len(suggested_topics)} topics")
            return suggested_topics
            
        except Exception as e:
            logger.error(f"Failed to suggest topics: {str(e)}")
            raise TopicSuggestionError(f"Topic suggestion failed: {str(e)}") from e
    
    async def select_topic(self, topic_id: str, session_id: UUID) -> Topic:
        """Select a topic for a conversation session.
        
        Args:
            topic_id: ID of the topic to select
            session_id: ID of the conversation session
            
        Returns:
            Selected topic
            
        Raises:
            TopicManagerError: If topic selection fails
        """
        try:
            logger.info(f"Selecting topic {topic_id} for session {session_id}")
            
            topic = await self.topic_repository.get_by_id(topic_id)
            if not topic:
                raise TopicManagerError(f"Topic not found: {topic_id}")
            
            logger.info(f"Successfully selected topic: {topic.name}")
            return topic
            
        except Exception as e:
            logger.error(f"Failed to select topic: {str(e)}")
            raise TopicManagerError(f"Topic selection failed: {str(e)}") from e
    
    async def generate_topic_starter(
        self, 
        topic: Topic, 
        user_level: ProficiencyLevel,
        target_language: str
    ) -> str:
        """Generate an AI-powered conversation starter for a topic.
        
        Args:
            topic: Topic to generate starter for
            user_level: User's proficiency level
            target_language: Target language for the starter
            
        Returns:
            Generated conversation starter
            
        Raises:
            TopicManagerError: If starter generation fails
        """
        try:
            logger.info(f"Generating starter for topic: {topic.name}")
            
            # Use existing conversation starters if available and appropriate
            if topic.conversation_starters:
                # Use AI to select and adapt the best starter
                starter = await self._ai_adapt_starter(
                    topic, user_level, target_language
                )
                if starter:
                    return starter
            
            # Generate new starter using AI
            starter = await self._ai_generate_starter(
                topic, user_level, target_language
            )
            
            logger.info("Successfully generated topic starter")
            return starter
            
        except Exception as e:
            logger.error(f"Failed to generate topic starter: {str(e)}")
            raise TopicManagerError(f"Starter generation failed: {str(e)}") from e
    
    async def check_topic_coherence(
        self, 
        messages: List[Message], 
        topic: Topic,
        threshold: Optional[float] = None
    ) -> bool:
        """Check if conversation messages are coherent with the selected topic.
        
        Args:
            messages: List of conversation messages
            topic: Current topic
            threshold: Coherence threshold (0.0-1.0)
            
        Returns:
            True if conversation is coherent with topic
            
        Raises:
            TopicCoherenceError: If coherence checking fails
        """
        try:
            if not messages:
                return True  # Empty conversation is coherent
            
            threshold = threshold or self._coherence_threshold
            logger.info(f"Checking topic coherence for {len(messages)} messages")
            
            # Get recent user messages for analysis
            recent_messages = [m for m in messages[-6:] if m.is_user_message()]
            if not recent_messages:
                return True
            
            # Use AI to analyze coherence
            coherence_score = await self._ai_analyze_coherence(
                recent_messages, topic
            )
            
            is_coherent = coherence_score >= threshold
            logger.info(f"Topic coherence score: {coherence_score:.2f}, coherent: {is_coherent}")
            
            return is_coherent
            
        except Exception as e:
            logger.error(f"Failed to check topic coherence: {str(e)}")
            raise TopicCoherenceError(f"Coherence checking failed: {str(e)}") from e
    
    async def detect_topic_transition(
        self, 
        messages: List[Message], 
        current_topic: Topic
    ) -> Optional[str]:
        """Detect if user wants to transition to a different topic.
        
        Args:
            messages: List of conversation messages
            current_topic: Current conversation topic
            
        Returns:
            Suggested new topic ID if transition detected, None otherwise
            
        Raises:
            TopicTransitionError: If transition detection fails
        """
        try:
            if not messages:
                return None
            
            logger.info("Detecting potential topic transition")
            
            # Get the last few user messages
            recent_messages = [m for m in messages[-3:] if m.is_user_message()]
            if not recent_messages:
                return None
            
            # Check for explicit transition keywords
            last_message = recent_messages[-1]
            if self._has_transition_keywords(last_message.content):
                logger.info("Explicit transition keywords detected")
                return await self._suggest_transition_topic(
                    last_message, current_topic
                )
            
            # Use AI to detect implicit topic transitions
            transition_topic = await self._ai_detect_transition(
                recent_messages, current_topic
            )
            
            if transition_topic:
                logger.info(f"AI detected topic transition to: {transition_topic}")
            
            return transition_topic
            
        except Exception as e:
            logger.error(f"Failed to detect topic transition: {str(e)}")
            raise TopicTransitionError(f"Transition detection failed: {str(e)}") from e
    
    async def get_related_topics(
        self, 
        current_topic: Topic, 
        user_level: ProficiencyLevel,
        limit: int = 3
    ) -> List[Topic]:
        """Get topics related to the current topic.
        
        Args:
            current_topic: Current conversation topic
            user_level: User's proficiency level
            limit: Maximum number of related topics
            
        Returns:
            List of related topics
        """
        try:
            logger.info(f"Getting related topics for: {current_topic.name}")
            
            # Get explicitly related topics from repository
            related_topics = await self.topic_repository.get_related_topics(
                current_topic.id, limit * 2
            )
            
            # Filter by user level suitability
            suitable_topics = [
                t for t in related_topics 
                if t.is_suitable_for_level(user_level)
            ]
            
            # If we don't have enough, get topics from same category
            if len(suitable_topics) < limit:
                category_topics = await self.topic_repository.get_by_category(
                    current_topic.category, limit * 2
                )
                
                for topic in category_topics:
                    if (topic.id != current_topic.id and 
                        topic.id not in [t.id for t in suitable_topics] and
                        topic.is_suitable_for_level(user_level)):
                        suitable_topics.append(topic)
                        if len(suitable_topics) >= limit:
                            break
            
            return suitable_topics[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get related topics: {str(e)}")
            return []  # Return empty list on error rather than raising
    
    # Private helper methods
    
    async def _get_base_topics(
        self, 
        user_preferences: LanguagePreferences, 
        limit: int
    ) -> List[Topic]:
        """Get base topics from repository based on user preferences."""
        if user_preferences.preferred_topics:
            # Get topics from preferred categories
            topics = await self.topic_repository.get_by_categories_and_level(
                user_preferences.preferred_topics,
                user_preferences.proficiency_level or ProficiencyLevel.A2,
                limit
            )
        else:
            # Get topics suitable for user level
            topics = await self.topic_repository.get_suitable_for_level(
                user_preferences.proficiency_level or ProficiencyLevel.A2,
                limit
            )
        
        return topics
    
    async def _ai_rank_topics(
        self, 
        topics: List[Topic], 
        user_preferences: LanguagePreferences,
        limit: int
    ) -> List[Topic]:
        """Use AI to rank and personalize topic suggestions."""
        if not topics:
            return []
        
        try:
            # Create prompt for AI ranking
            prompt = self._create_ranking_prompt(topics, user_preferences)
            
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.default_model,
                max_tokens=500,
                temperature=0.3
            )
            
            response = await self.llm_service.generate_response(request)
            
            # Parse AI response to get ranked topic IDs
            ranked_ids = self._parse_ranking_response(response.content)
            
            # Return topics in AI-suggested order
            ranked_topics = []
            for topic_id in ranked_ids:
                topic = next((t for t in topics if t.id == topic_id), None)
                if topic:
                    ranked_topics.append(topic)
                if len(ranked_topics) >= limit:
                    break
            
            # Fill remaining slots with original order if needed
            for topic in topics:
                if topic.id not in ranked_ids and len(ranked_topics) < limit:
                    ranked_topics.append(topic)
            
            return ranked_topics[:limit]
            
        except LLMServiceError:
            # Fallback to original order on AI failure
            return topics[:limit]
    
    async def _ai_adapt_starter(
        self, 
        topic: Topic, 
        user_level: ProficiencyLevel,
        target_language: str
    ) -> Optional[str]:
        """Use AI to adapt existing conversation starters."""
        try:
            prompt = self._create_starter_adaptation_prompt(
                topic, user_level, target_language
            )
            
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.default_model,
                max_tokens=200,
                temperature=0.7
            )
            
            response = await self.llm_service.generate_response(request)
            return response.content.strip()
            
        except LLMServiceError:
            return None
    
    async def _ai_generate_starter(
        self, 
        topic: Topic, 
        user_level: ProficiencyLevel,
        target_language: str
    ) -> str:
        """Generate new conversation starter using AI."""
        prompt = self._create_starter_generation_prompt(
            topic, user_level, target_language
        )
        
        request = LLMRequest(
            messages=[{"role": "user", "content": prompt}],
            model=self.default_model,
            max_tokens=200,
            temperature=0.7
        )
        
        response = await self.llm_service.generate_response(request)
        return response.content.strip()
    
    async def _ai_analyze_coherence(
        self, 
        messages: List[Message], 
        topic: Topic
    ) -> float:
        """Use AI to analyze topic coherence."""
        prompt = self._create_coherence_prompt(messages, topic)
        
        request = LLMRequest(
            messages=[{"role": "user", "content": prompt}],
            model=self.default_model,
            max_tokens=100,
            temperature=0.1
        )
        
        response = await self.llm_service.generate_response(request)
        
        # Parse coherence score from response
        return self._parse_coherence_score(response.content)
    
    async def _ai_detect_transition(
        self, 
        messages: List[Message], 
        current_topic: Topic
    ) -> Optional[str]:
        """Use AI to detect topic transitions."""
        try:
            prompt = self._create_transition_prompt(messages, current_topic)
            
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.default_model,
                max_tokens=200,
                temperature=0.3
            )
            
            response = await self.llm_service.generate_response(request)
            
            # Parse transition suggestion from response
            return self._parse_transition_response(response.content)
            
        except LLMServiceError:
            return None
    
    def _has_transition_keywords(self, message_content: str) -> bool:
        """Check if message contains explicit transition keywords."""
        content_lower = message_content.lower()
        return any(keyword in content_lower for keyword in self._transition_keywords)
    
    async def _suggest_transition_topic(
        self, 
        message: Message, 
        current_topic: Topic
    ) -> Optional[str]:
        """Suggest a transition topic based on explicit user request."""
        try:
            # Use AI to extract topic from user's transition request
            prompt = f"""
            The user said: "{message.content}"
            
            They want to change from the current topic "{current_topic.name}" to something else.
            What topic are they interested in discussing? Respond with just the topic name or "unknown" if unclear.
            """
            
            request = LLMRequest(
                messages=[{"role": "user", "content": prompt}],
                model=self.default_model,
                max_tokens=50,
                temperature=0.3
            )
            
            response = await self.llm_service.generate_response(request)
            suggested_topic = response.content.strip().lower()
            
            if suggested_topic == "unknown":
                return None
            
            # Try to find matching topic in repository
            topics = await self.topic_repository.search_by_keyword(suggested_topic, 5)
            return topics[0].id if topics else None
            
        except Exception:
            return None
    
    # Prompt creation methods
    
    def _create_ranking_prompt(
        self, 
        topics: List[Topic], 
        user_preferences: LanguagePreferences
    ) -> str:
        """Create prompt for AI topic ranking."""
        topics_text = "\n".join([
            f"- {t.id}: {t.name} ({t.category.value}, {t.difficulty_level.value})"
            for t in topics
        ])
        
        preferred_categories = ", ".join([
            cat.value for cat in user_preferences.preferred_topics
        ]) if user_preferences.preferred_topics else "none specified"
        
        goals = ", ".join(user_preferences.learning_goals) if user_preferences.learning_goals else "general learning"
        
        return f"""
        Rank these conversation topics for a language learner:
        
        Topics:
        {topics_text}
        
        User preferences:
        - Level: {user_preferences.proficiency_level.value if user_preferences.proficiency_level else 'A2'}
        - Preferred categories: {preferred_categories}
        - Learning goals: {goals}
        - Languages: {user_preferences.native_language} → {user_preferences.target_language}
        
        Rank the topics by relevance and engagement potential. Respond with topic IDs in order, one per line.
        """
    
    def _create_starter_adaptation_prompt(
        self, 
        topic: Topic, 
        user_level: ProficiencyLevel,
        target_language: str
    ) -> str:
        """Create prompt for adapting conversation starters."""
        starters = "\n".join([f"- {s}" for s in topic.conversation_starters])
        
        return f"""
        Adapt one of these conversation starters for a {user_level.value} level learner in {target_language}:
        
        Topic: {topic.name}
        Starters:
        {starters}
        
        Make it appropriate for their level and engaging. Respond with just the adapted starter.
        """
    
    def _create_starter_generation_prompt(
        self, 
        topic: Topic, 
        user_level: ProficiencyLevel,
        target_language: str
    ) -> str:
        """Create prompt for generating new conversation starters."""
        return f"""
        Create an engaging conversation starter in {target_language} for a {user_level.value} level learner.
        
        Topic: {topic.name}
        Description: {topic.description}
        Keywords: {', '.join(topic.keywords)}
        
        Make it appropriate for their level, interesting, and likely to generate discussion.
        Respond with just the conversation starter.
        """
    
    def _create_coherence_prompt(self, messages: List[Message], topic: Topic) -> str:
        """Create prompt for coherence analysis."""
        messages_text = "\n".join([
            f"User: {m.content}" for m in messages
        ])
        
        return f"""
        Analyze how well these user messages relate to the topic "{topic.name}".
        
        Topic description: {topic.description}
        Topic keywords: {', '.join(topic.keywords)}
        
        Messages:
        {messages_text}
        
        Rate coherence from 0.0 (completely off-topic) to 1.0 (perfectly on-topic).
        Respond with just the number (e.g., 0.8).
        """
    
    def _create_transition_prompt(
        self, 
        messages: List[Message], 
        current_topic: Topic
    ) -> str:
        """Create prompt for transition detection."""
        messages_text = "\n".join([
            f"User: {m.content}" for m in messages
        ])
        
        return f"""
        The user is discussing "{current_topic.name}". Analyze if they want to change topics:
        
        Recent messages:
        {messages_text}
        
        If they want to change topics, suggest what they want to discuss.
        If they're staying on topic, respond with "no_transition".
        Respond with just the new topic name or "no_transition".
        """
    
    # Response parsing methods
    
    def _parse_ranking_response(self, response: str) -> List[str]:
        """Parse AI ranking response to extract topic IDs."""
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        topic_ids = []
        
        for line in lines:
            # Extract topic ID (handle various formats)
            if ':' in line:
                # Format: "topic_id: description" or "1. topic_id: description"
                parts = line.split(':')
                topic_part = parts[0].strip()
                # Remove numbering like "1. " from the beginning
                import re
                topic_id = re.sub(r'^\d+\.\s*', '', topic_part).strip()
            elif line.startswith('-'):
                # Format: "- topic_id"
                topic_id = line[1:].strip()
            else:
                # Format: just "topic_id" or "1. topic_id"
                import re
                topic_id = re.sub(r'^\d+\.\s*', '', line).strip()
            
            if topic_id:
                topic_ids.append(topic_id)
        
        return topic_ids
    
    def _parse_coherence_score(self, response: str) -> float:
        """Parse coherence score from AI response."""
        try:
            # Extract number from response (including negative numbers)
            import re
            match = re.search(r'(-?\d+\.?\d*)', response)
            if match:
                score = float(match.group(1))
                return max(0.0, min(1.0, score))  # Clamp to 0-1 range
        except (ValueError, AttributeError):
            pass
        
        # Default to neutral coherence on parsing failure
        return 0.5
    
    def _parse_transition_response(self, response: str) -> Optional[str]:
        """Parse transition response from AI."""
        response = response.strip().lower()
        
        if response == "no_transition" or "no transition" in response:
            return None
        
        # Return the suggested topic (clean up the response)
        return response.replace("topic:", "").strip() if response else None