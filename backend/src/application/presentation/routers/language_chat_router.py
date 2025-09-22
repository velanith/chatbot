"""Language learning chat router with session memory."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from src.application.services.session_memory_service import SessionMemoryService
from src.application.services.openrouter_service import OpenRouterService

router = APIRouter()

# Global service instances
session_memory_service = None
openrouter_service = None


def get_session_memory_service():
    """Get or create session memory service instance."""
    global session_memory_service
    if session_memory_service is None:
        session_memory_service = SessionMemoryService()
    return session_memory_service


def get_openrouter_service():
    """Get or create OpenRouter service instance."""
    global openrouter_service
    if openrouter_service is None:
        openrouter_service = OpenRouterService()
    return openrouter_service


# Pydantic models
class LanguageChatRequest(BaseModel):
    content: str
    session_id: Optional[str] = None


class LanguageChatResponse(BaseModel):
    role: str
    content: str
    session_id: str
    message_count: Optional[int] = None
    timestamp: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    message_count: int
    last_message: str


class SimpleMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class SimpleChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[SimpleMessage]] = []


class SimpleChatResponse(BaseModel):
    response: str
    timestamp: str
    model_used: str


@router.post("/language-learning", response_model=LanguageChatResponse)
async def language_learning_chat(request: LanguageChatRequest):
    """Language learning chat with session memory."""
    try:
        service = get_session_memory_service()

        # Load or create session
        if request.session_id:
            if not service.load_session(request.session_id):
                session_id = await service.create_new_session()
            else:
                session_id = request.session_id
        else:
            session_id = await service.create_new_session()

        # Send message with memory
        response = await service.send_message_with_memory(request.content)

        return LanguageChatResponse(
            role="assistant",
            content=response,
            session_id=service.current_session_id,
            message_count=len(service.chat_history),
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions", response_model=List[SessionInfo])
async def list_language_sessions():
    """List all language learning sessions."""
    try:
        service = get_session_memory_service()
        sessions = service.list_sessions()

        result = []
        for session in sessions:
            result.append(
                SessionInfo(
                    session_id=session["session_id"],
                    created_at=session["created_at"],
                    message_count=session["message_count"],
                    last_message=session["last_message"],
                )
            )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get messages from a specific session."""
    try:
        service = get_session_memory_service()

        if service.load_session(session_id):
            messages = []
            for msg in service.chat_history:
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
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/sessions/new")
async def create_new_language_session():
    """Create new language learning session."""
    try:
        service = get_session_memory_service()
        session_id = await service.create_new_session()

        return {
            "session_id": session_id,
            "message": "New language learning session created successfully",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_language_session(session_id: str):
    """Delete a language learning session."""
    try:
        service = get_session_memory_service()
        
        if service.delete_session(session_id):
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/sessions/{session_id}/reset")
async def reset_language_session(session_id: str):
    """Reset session keeping only system prompt."""
    try:
        service = get_session_memory_service()

        if service.load_session(session_id):
            if service.reset_session_with_system_prompt():
                return {"message": f"Session {session_id} reset successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to reset session")
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions/{session_id}/export")
async def export_language_session(session_id: str):
    """Export session to text file."""
    try:
        service = get_session_memory_service()
        result = service.export_session(session_id)

        success = "export edildi" in result or "exported" in result
        return {"message": result, "success": success}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/simple", response_model=SimpleChatResponse)
async def simple_language_chat(request: SimpleChatRequest):
    """Simple language chat without memory."""
    try:
        service = get_openrouter_service()

        # Prepare messages
        messages = []
        for msg in request.chat_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Add new user message
        messages.append({"role": "user", "content": request.message})

        # Send to API
        response = await service.send_message(messages)

        return SimpleChatResponse(
            response=response,
            timestamp=datetime.now().isoformat(),
            model_used="gpt-oss-20b",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/quick")
async def quick_language_chat(message_data: dict):
    """Quick language chat."""
    try:
        message = message_data.get("message", "")
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        service = get_openrouter_service()

        # Send message
        messages = [{"role": "user", "content": message}]
        response = await service.send_message(messages)

        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "gpt-oss-20b",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/status")
async def language_chat_status():
    """Check language chat service status."""
    try:
        service = get_openrouter_service()
        connection_ok = await service.test_connection()

        return {
            "status": "ready" if connection_ok else "error",
            "message": "Language chat service is running" if connection_ok else "API connection failed",
            "model": "gpt-oss-20b",
            "has_api_key": bool(service.api_key),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }