"""Chatbot router for AI conversation endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.presentation.schemas.chat_schemas import (
    ChatbotRequest,
    ChatbotResponse,
    SessionCreateRequest,
    SessionResponse,
    MessageResponse,
    MemoryChatRequest,
    MemoryChatResponse,
    SessionInfo
)
from src.application.use_cases.chatbot_use_case import ChatbotUseCase, ChatbotRequest as UseCaseRequest
from src.application.services.session_memory_service import SessionMemoryService
from src.presentation.dependencies import get_chatbot_use_case
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["chatbot"])

# Global memory service instance
memory_service = None


def get_memory_service():
    """Get or create memory service instance."""
    global memory_service
    if memory_service is None:
        memory_service = SessionMemoryService()
    return memory_service


@router.post("/message", response_model=ChatbotResponse)
async def send_message(
    request: ChatbotRequest,
    chatbot_use_case: ChatbotUseCase = Depends(get_chatbot_use_case)
):
    """Send message to AI chatbot."""
    try:
        use_case_request = UseCaseRequest(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            include_history=request.include_history,
            max_history_messages=request.max_history_messages
        )
        
        response = await chatbot_use_case.send_message(use_case_request)
        
        return ChatbotResponse(
            response=response.response,
            session_id=response.session_id,
            message_count=response.message_count,
            timestamp=response.timestamp,
            model_used=response.model_used
        )
        
    except Exception as e:
        logger.error(f"Chatbot message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Memory-based chat endpoints (from backend)
@router.post("/memory", response_model=MemoryChatResponse)
async def chat_with_memory(request: MemoryChatRequest):
    """Memory-based chat endpoint."""
    try:
        logger.info(f"Memory chat request: role={request.role}, session_id={request.session_id}")
        
        memory_svc = get_memory_service()
        
        # Load or create session
        if request.session_id:
            if not memory_svc.load_session(request.session_id):
                logger.info(f"Session not found: {request.session_id}, creating new one")
                session_id = memory_svc.create_new_session()
            else:
                session_id = request.session_id
        else:
            logger.info("Creating new session")
            session_id = memory_svc.create_new_session()
        
        # Send message
        response = await memory_svc.send_message_with_memory(request.content)
        
        return MemoryChatResponse(
            role="assistant",
            content=response,
            session_id=memory_svc.current_session_id,
            message_count=len(memory_svc.chat_history),
            timestamp=datetime.now().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Memory chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """List all chat sessions."""
    try:
        memory_svc = get_memory_service()
        sessions = memory_svc.list_sessions()
        
        return [
            SessionInfo(
                session_id=session["session_id"],
                created_at=session["created_at"],
                message_count=session["message_count"],
                last_message=session["last_message"],
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"List sessions error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages_memory(session_id: str):
    """Get messages from a memory session."""
    try:
        memory_svc = get_memory_service()
        
        if memory_svc.load_session(session_id):
            messages = []
            for msg in memory_svc.chat_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": msg.get("timestamp", ""),
                })
            
            return {
                "session_id": session_id,
                "messages": messages,
                "total_messages": len(messages),
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Get session messages error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/sessions/new")
async def create_new_session():
    """Create new memory session."""
    try:
        memory_svc = get_memory_service()
        session_id = memory_svc.create_new_session()
        
        return {
            "session_id": session_id,
            "message": "New session created successfully",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Create session error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session_memory(session_id: str):
    """Delete a memory session."""
    try:
        memory_svc = get_memory_service()
        
        if memory_svc.delete_session(session_id):
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/sessions/{session_id}/clear")
async def clear_session_memory(session_id: str):
    """Clear a memory session."""
    try:
        memory_svc = get_memory_service()
        
        if memory_svc.load_session(session_id):
            memory_svc.clear_session()
            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Clear session error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str):
    """Export a memory session."""
    try:
        memory_svc = get_memory_service()
        result = memory_svc.export_session(session_id)
        
        success = "export edildi" in result
        return {"message": result, "success": success}
        
    except Exception as e:
        logger.error(f"Export session error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Simple chat endpoints (without memory)
@router.post("/simple", response_model=Dict[str, Any])
async def simple_chat(request: Dict[str, Any]):
    """Simple chat without memory."""
    try:
        from src.application.services.openrouter_chatbot_service import OpenRouterChatbotService
        
        message = request.get("message", "")
        chat_history = request.get("chat_history", [])
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        chatbot_service = OpenRouterChatbotService()
        
        # Prepare messages
        messages = []
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})
        
        # Send to API
        response = await chatbot_service.send_message(messages)
        
        if "choices" in response and len(response["choices"]) > 0:
            bot_message = response["choices"][0]["message"]["content"]
        else:
            bot_message = "No response"
        
        return {
            "response": bot_message,
            "timestamp": datetime.now().isoformat(),
            "model_used": "gpt-oss-20b",
        }
        
    except Exception as e:
        logger.error(f"Simple chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/quick")
async def quick_chat(message_data: Dict[str, str]):
    """Quick chat endpoint."""
    try:
        from src.application.services.openrouter_chatbot_service import OpenRouterChatbotService
        
        message = message_data.get("message", "")
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        chatbot_service = OpenRouterChatbotService()
        
        messages = [{"role": "user", "content": message}]
        response = await chatbot_service.send_message(messages)
        
        if "choices" in response and len(response["choices"]) > 0:
            bot_message = response["choices"][0]["message"]["content"]
        else:
            bot_message = "No response"
        
        return {
            "response": bot_message,
            "timestamp": datetime.now().isoformat(),
            "model": "gpt-oss-20b",
        }
        
    except Exception as e:
        logger.error(f"Quick chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/status")
async def chat_status():
    """Check chat service status."""
    try:
        from src.application.services.openrouter_chatbot_service import OpenRouterChatbotService
        
        chatbot_service = OpenRouterChatbotService()
        has_api_key = bool(chatbot_service.api_key)
        
        return {
            "status": "ready" if has_api_key else "error",
            "message": "Chat service is running" if has_api_key else "API key not configured",
            "model": "gpt-oss-20b",
            "has_api_key": has_api_key,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Chat status error: {e}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }


@router.get("/test")
async def test_chatbot(
    chatbot_use_case: ChatbotUseCase = Depends(get_chatbot_use_case)
):
    """Test chatbot connection."""
    try:
        is_connected = await chatbot_use_case.test_chatbot_connection()
        
        return {
            "status": "connected" if is_connected else "disconnected",
            "message": "Chatbot connection test completed"
        }
        
    except Exception as e:
        logger.error(f"Chatbot test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))