"""Session memory service for chatbot conversations."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.infrastructure.logging import get_logger
from src.application.services.openrouter_chatbot_service import OpenRouterChatbotService

logger = get_logger(__name__)


class SessionMemoryService:
    """Session-based memory management for chatbot conversations."""
    
    def __init__(self, sessions_dir: str = "chat_sessions"):
        """Initialize session memory service."""
        self.sessions_dir = Path(sessions_dir)
        self.current_session_id: Optional[str] = None
        self.chat_history: List[Dict[str, Any]] = []
        self.chatbot_service = OpenRouterChatbotService()
        self.ensure_sessions_dir()
    
    def ensure_sessions_dir(self):
        """Ensure sessions directory exists."""
        self.sessions_dir.mkdir(exist_ok=True)
        logger.info(f"Sessions directory ensured: {self.sessions_dir}")
    
    def get_session_file(self, session_id: str) -> Path:
        """Get session file path."""
        return self.sessions_dir / f"{session_id}.json"
    
    def create_new_session(self) -> str:
        """Create new session with system prompt."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session_id = session_id
        
        # Initialize with system prompt
        initial_messages = [
            {
                "role": "system",
                "content": self.chatbot_service.get_system_prompt(),
                "timestamp": datetime.now().isoformat(),
            }
        ]
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": initial_messages,
        }
        
        try:
            session_file = self.get_session_file(session_id)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.chat_history = initial_messages.copy()
            logger.info(f"New session created: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise Exception(f"Session creation failed: {e}")
    
    def load_session(self, session_id: str) -> bool:
        """Load existing session."""
        session_file = self.get_session_file(session_id)
        
        if not session_file.exists():
            logger.warning(f"Session not found: {session_id}")
            return False
        
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            self.current_session_id = session_id
            messages = session_data.get("messages", [])
            
            # Ensure system prompt exists
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                system_message = {
                    "role": "system",
                    "content": self.chatbot_service.get_system_prompt(),
                    "timestamp": datetime.now().isoformat(),
                }
                messages.insert(0, system_message)
                logger.info("Added system prompt to session")
            
            self.chat_history = messages
            logger.info(f"Session loaded: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return False
    
    def save_session(self) -> bool:
        """Save current session."""
        if not self.current_session_id:
            logger.warning("No active session to save")
            return False
        
        session_data = {
            "session_id": self.current_session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": self.chat_history,
            "total_messages": len(self.chat_history),
        }
        
        try:
            session_file = self.get_session_file(self.current_session_id)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Session saved: {self.current_session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        sessions = []
        
        if not self.sessions_dir.exists():
            return sessions
        
        for session_file in self.sessions_dir.glob("*.json"):
            session_id = session_file.stem
            
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                
                # Get last message preview
                last_message = "Henüz mesaj yok"
                messages = session_data.get("messages", [])
                user_messages = [
                    m for m in messages if m.get("role") in ["user", "assistant"]
                ]
                
                if user_messages:
                    last_msg = user_messages[-1]
                    preview = last_msg["content"][:50]
                    if len(last_msg["content"]) > 50:
                        preview += "..."
                    role_emoji = "👤" if last_msg["role"] == "user" else "🤖"
                    last_message = f"{role_emoji} {preview}"
                
                sessions.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "message_count": len(user_messages),
                    "last_message": last_message,
                })
                
            except Exception as e:
                logger.error(f"Failed to read session {session_file}: {e}")
        
        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions
    
    async def send_message_with_memory(self, message: str) -> str:
        """Send message with session memory."""
        if not self.current_session_id:
            logger.info("No active session, creating new one")
            self.create_new_session()
        
        # Add user message
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.chat_history.append(user_message)
        
        try:
            # Manage conversation length
            self.manage_conversation_length()
            
            # Prepare messages for API
            api_messages = []
            for msg in self.chat_history:
                api_messages.append({
                    "role": msg["role"], 
                    "content": msg["content"]
                })
            
            # Send to OpenRouter API
            response = await self.chatbot_service.send_message(api_messages)
            
            if "choices" in response and len(response["choices"]) > 0:
                bot_response = response["choices"][0]["message"]["content"]
                
                # Add bot response
                bot_message = {
                    "role": "assistant",
                    "content": bot_response,
                    "timestamp": datetime.now().isoformat(),
                }
                self.chat_history.append(bot_message)
                
                # Save session
                self.save_session()
                
                logger.info("Message sent and response received successfully")
                return bot_response
            else:
                raise Exception("No response from API")
                
        except Exception as e:
            # Remove user message on error
            if self.chat_history and self.chat_history[-1]["role"] == "user":
                self.chat_history.pop()
            logger.error(f"Failed to send message: {e}")
            raise e
    
    def manage_conversation_length(self):
        """Manage conversation length for memory efficiency."""
        max_messages = 41  # 40 messages + 1 system prompt
        
        if len(self.chat_history) > max_messages:
            # Keep system messages
            system_messages = [
                m for m in self.chat_history if m.get("role") == "system"
            ]
            other_messages = [
                m for m in self.chat_history if m.get("role") != "system"
            ]
            
            # Keep last 40 messages
            other_messages = other_messages[-(max_messages - 1):]
            self.chat_history = system_messages + other_messages
            
            logger.info(f"Chat history limited to {max_messages} messages")
    
    def clear_session(self) -> bool:
        """Clear current session but keep system prompt."""
        if not self.current_session_id:
            logger.warning("No active session to clear")
            return False
        
        # Keep only system prompt
        system_message = {
            "role": "system",
            "content": self.chatbot_service.get_system_prompt(),
            "timestamp": datetime.now().isoformat(),
        }
        
        self.chat_history = [system_message]
        self.save_session()
        
        logger.info("Session cleared, system prompt retained")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session_file = self.get_session_file(session_id)
        
        if not session_file.exists():
            logger.warning(f"Session not found for deletion: {session_id}")
            return False
        
        try:
            session_file.unlink()
            
            # Clear current session if it's the one being deleted
            if self.current_session_id == session_id:
                self.current_session_id = None
                self.chat_history = []
            
            logger.info(f"Session deleted: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def export_session(self, session_id: Optional[str] = None) -> str:
        """Export session to text file."""
        target_session = session_id or self.current_session_id
        
        if not target_session:
            return "❌ No session to export"
        
        session_file = self.get_session_file(target_session)
        if not session_file.exists():
            return "❌ Session file not found"
        
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            # Create export file
            export_filename = f"{target_session}_export.txt"
            export_path = self.sessions_dir / export_filename
            
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(f"Sohbet Export - {target_session}\n")
                f.write(f"Oluşturulma Tarihi: {session_data.get('created_at', 'Bilinmiyor')}\n")
                
                messages = session_data.get("messages", [])
                user_messages = [
                    m for m in messages if m.get("role") in ["user", "assistant"]
                ]
                
                f.write(f"Toplam Mesaj: {len(user_messages)}\n")
                f.write("=" * 50 + "\n\n")
                
                # System prompt
                system_msg = next(
                    (m for m in messages if m.get("role") == "system"), None
                )
                if system_msg:
                    f.write("🤖 SYSTEM PROMPT:\n")
                    f.write(f"   {system_msg['content']}\n")
                    f.write("=" * 50 + "\n\n")
                
                # User messages
                counter = 1
                for msg in messages:
                    if msg.get("role") in ["user", "assistant"]:
                        role_name = "SEN" if msg["role"] == "user" else "GPT-OSS"
                        timestamp = msg.get("timestamp", "Bilinmiyor")
                        f.write(f"{counter:3d}. [{timestamp}] {role_name}:\n")
                        f.write(f"     {msg['content']}\n\n")
                        counter += 1
            
            logger.info(f"Session exported: {export_path}")
            return f"✅ Session exported: {export_path}"
            
        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return f"❌ Export error: {e}"
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        if not self.current_session_id:
            return {"error": "No active session"}
        
        user_messages = [
            m for m in self.chat_history if m.get("role") in ["user", "assistant"]
        ]
        has_system = any(m.get("role") == "system" for m in self.chat_history)
        
        info = {
            "session_id": self.current_session_id,
            "user_messages": len(user_messages),
            "has_system_prompt": has_system,
            "total_messages": len(self.chat_history),
        }
        
        if user_messages:
            info["first_message"] = user_messages[0].get("timestamp", "Unknown")
            info["last_message"] = user_messages[-1].get("timestamp", "Unknown")
        
        return info