from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from chatbot.bot import GPTOSSChatbot  # Class'ı import et

router = APIRouter()

# Global chatbot instance (session başına ayrı olması daha iyi olur)
# Ama basit kullanım için global tanımlayabiliriz
chatbot_instance = None

def get_chatbot():
    """Chatbot instance'ını al veya oluştur"""
    global chatbot_instance
    if chatbot_instance is None:
        chatbot_instance = GPTOSSChatbot()
    return chatbot_instance

# Pydantic models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    model_used: str

# AI Chat Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: Request, chat_request: ChatRequest):
    """AI ile sohbet endpoint'i - GPTOSSChatbot class'ını kullanır"""
    try:
        # Chatbot instance'ını al
        chatbot = get_chatbot()
        
        # Chat history'yi hazırla
        messages = []
        for msg in chat_request.chat_history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Yeni kullanıcı mesajını ekle
        messages.append({"role": "user", "content": chat_request.message})
        
        # GPTOSSChatbot'un query_chatbot metodunu kullan
        output = chatbot.query_chatbot(messages)
        
        # Yanıtı işle
        if "choices" in output and len(output["choices"]) > 0:
            bot_message = output["choices"][0]["message"]["content"]
        else:
            bot_message = "No response"
        
        return ChatResponse(
            response=bot_message,
            timestamp=datetime.now().isoformat(),
            model_used="gpt-oss-20b"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/chat/simple")
async def simple_chat(request: Request, message_data: dict):
    """Basit chat endpoint'i - GPTOSSChatbot class'ını kullanır"""
    try:
        message = message_data.get("message", "")
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Chatbot instance'ını al
        chatbot = get_chatbot()
        
        # GPTOSSChatbot'un query_chatbot metodunu kullan
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
            "model": "gpt-oss-20b"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Chatbot durumunu kontrol etme endpoint'i
@router.get("/chat/status")
async def chat_status():
    """Chatbot durumunu kontrol et"""
    try:
        chatbot = get_chatbot()
        
        # API key kontrolü
        if not chatbot.api_key:
            return {
                "status": "error",
                "message": "API key not found",
                "timestamp": datetime.now().isoformat()
            }
        
        # Bağlantı testi (opsiyonel - yavaş olabilir)
        # connection_test = chatbot.test_connection()
        
        return {
            "status": "ready",
            "message": "Chatbot is ready",
            "model": "gpt-oss-20b",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Chat history ile gelişmiş endpoint
@router.post("/chat/advanced")
async def advanced_chat(request: Request, chat_request: ChatRequest):
    """Gelişmiş chat endpoint'i - session management ile"""
    try:
        # Her session için ayrı chatbot instance'ı olması daha iyi olur
        # Ama şimdilik global kullanıyoruz
        chatbot = get_chatbot()
        
        # Eğer chat history boşsa, chatbot'un kendi history'sini temizle
        if not chat_request.chat_history:
            chatbot.clear_history()
        else:
            # Chat history'yi chatbot'un kendi history'sine yükle
            chatbot.chat_history = []
            for msg in chat_request.chat_history:
                chatbot.chat_history.append({"role": msg.role, "content": msg.content})
        
        # Yeni mesajı gönder ve yanıtı al
        try:
            # send_message metodunu bot.py'ye eklememiz gerekiyor
            # Şimdilik query_chatbot kullanıyoruz
            chatbot.chat_history.append({"role": "user", "content": chat_request.message})
            
            output = chatbot.query_chatbot(chatbot.chat_history)
            
            if "choices" in output and len(output["choices"]) > 0:
                bot_message = output["choices"][0]["message"]["content"]
                chatbot.chat_history.append({"role": "assistant", "content": bot_message})
            else:
                bot_message = "No response"
            
            # Updated chat history'yi döndür
            updated_history = []
            for msg in chatbot.chat_history:
                updated_history.append(ChatMessage(role=msg["role"], content=msg["content"]))
            
            return {
                "response": bot_message,
                "chat_history": updated_history,
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-oss-20b"
            }
            
        except Exception as e:
            # Hata durumunda son kullanıcı mesajını çıkar
            if chatbot.chat_history and chatbot.chat_history[-1]["role"] == "user":
                chatbot.chat_history.pop()
            raise e
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Test endpoint'i
@router.post("/chat/test")
async def test_chat():
    """Chatbot bağlantısını test et"""
    try:
        chatbot = get_chatbot()
        
        if chatbot.test_connection():
            return {
                "status": "success",
                "message": "Chatbot connection test successful",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error", 
                "message": "Chatbot connection test failed",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")