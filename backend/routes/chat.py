from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from chatbot.memory_bot import SessionMemoryChatbot

router = APIRouter()

# Global chatbot instance
memory_chatbot = None


def get_memory_chatbot():
    """Memory chatbot instance'ını al veya oluştur"""
    global memory_chatbot
    if memory_chatbot is None:
        memory_chatbot = SessionMemoryChatbot()
        # API key kontrolü
        if not memory_chatbot.api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
    return memory_chatbot


# Pydantic models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class MemoryChatRequest(BaseModel):
    role: str
    content: str
    session_id: Optional[str] = None


class MemoryChatResponse(BaseModel):
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


class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    timestamp: str
    model_used: str


# Memory'li chat endpoint'leri
@router.post("/memory", response_model=MemoryChatResponse)
async def chat_with_memory(request: MemoryChatRequest):
    """Memory'li sohbet endpoint'i"""
    try:
        print(
            f"Request alındı: role={request.role}, content='{request.content[:50]}...', session_id={request.session_id}"
        )

        bot = get_memory_chatbot()

        # Session yükle veya oluştur
        if request.session_id:
            if not bot.load_session(request.session_id):
                print(f"Session bulunamadı: {request.session_id}")
                session_id = bot.create_new_session()
                print(f"Yeni session oluşturuldu: {session_id}")
            else:
                print(f"Session yüklendi: {request.session_id}")
                session_id = request.session_id
        else:
            print("Yeni session oluşturuluyor")
            session_id = bot.create_new_session()

        print(f"🤖 Mesaj gönderiliyor: '{request.content}'")

        # DÜZELTME: request.message değil request.content
        response = bot.send_message_with_memory(request.content)

        print(f"Yanıt alındı: '{response[:50]}...'")

        # DÜZELTME: Doğru field'ları kullan
        return MemoryChatResponse(
            role="assistant",
            content=response,  # response field'ı değil, content
            session_id=bot.current_session_id,
            message_count=len(bot.chat_history),
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        print(f"HATA DETAYI: {type(e).__name__}: {str(e)}")
        import traceback

        print(f"STACK TRACE: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """Tüm session'ları listele"""
    try:
        bot = get_memory_chatbot()
        sessions = bot.list_sessions()

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
    """Session'daki mesajları getir"""
    try:
        bot = get_memory_chatbot()

        if bot.load_session(session_id):
            messages = []
            for msg in bot.chat_history:
                messages.append(
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg.get("timestamp", ""),
                    }
                )

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
async def create_new_session():
    """Yeni session oluştur"""
    try:
        bot = get_memory_chatbot()
        session_id = bot.create_new_session()

        return {
            "session_id": session_id,
            "message": "New session created successfully",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Session'ı sil"""
    try:
        bot = get_memory_chatbot()
        session_file = bot.get_session_file(session_id)

        import os

        if os.path.exists(session_file):
            os.remove(session_file)

            # Eğer silinmekte olan session aktifse, temizle
            if bot.current_session_id == session_id:
                bot.current_session_id = None
                bot.chat_history = []

            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """Session'ı temizle"""
    try:
        bot = get_memory_chatbot()

        if bot.load_session(session_id):
            bot.chat_history = []
            bot.save_session()

            return {"message": f"Session {session_id} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str):
    """Session'ı export et"""
    try:
        bot = get_memory_chatbot()
        result = bot.export_session(session_id)

        if "export edildi" in result:
            return {"message": result, "success": True}
        else:
            return {"message": result, "success": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Basit chat endpoint'leri (memory olmadan)
@router.post(
    "/simple", response_model=ChatResponse, operation_id="simple_chat_endpoint"
)
async def simple_chat(request: ChatRequest):
    """Basit sohbet (memory'siz)"""
    try:
        from chatbot.bot import GPTOSSChatbot

        # Normal chatbot (memory'siz)
        chatbot = GPTOSSChatbot()

        if not chatbot.api_key:
            raise HTTPException(status_code=500, detail="API key not configured")

        # Chat history'yi hazırla
        messages = []
        for msg in request.chat_history:
            messages.append({"role": msg.role, "content": msg.content})

        # Yeni kullanıcı mesajını ekle
        messages.append({"role": "user", "content": request.message})

        # API'ye gönder
        output = chatbot.query_chatbot(messages)

        # Yanıtı işle
        if "choices" in output and len(output["choices"]) > 0:
            bot_message = output["choices"][0]["message"]["content"]
        else:
            bot_message = "No response"

        return ChatResponse(
            response=bot_message,
            timestamp=datetime.now().isoformat(),
            model_used="gpt-oss-20b",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/quick")
async def quick_chat(message_data: dict):
    """Hızlı sohbet"""
    try:
        from chatbot.bot import GPTOSSChatbot

        message = message_data.get("message", "")
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        chatbot = GPTOSSChatbot()

        if not chatbot.api_key:
            raise HTTPException(status_code=500, detail="API key not configured")

        # API'ye gönder
        messages = [{"role": "user", "content": message}]
        output = chatbot.query_chatbot(messages)

        # Yanıtı işle
        if "choices" in output and len(output["choices"]) > 0:
            bot_message = output["choices"][0]["message"]["content"]
        else:
            bot_message = "No response"

        return {
            "response": bot_message,
            "timestamp": datetime.now().isoformat(),
            "model": "gpt-oss-20b",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/status", operation_id="chat_status_endpoint")
async def chat_status():
    """Chat durumunu kontrol et"""
    try:
        bot = get_memory_chatbot()

        return {
            "status": "ready",
            "message": "Chat service is running",
            "model": "gpt-oss-20b",
            "has_api_key": bool(bot.api_key),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }
