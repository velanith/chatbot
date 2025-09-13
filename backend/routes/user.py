from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
import requests
import os
from pydantic import BaseModel
from typing import List, Optional
from chatbot.bot import query_chatbot


router = APIRouter()

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
    """AI ile sohbet endpoint'i - bot.py'deki query_chatbot fonksiyonunu kullanır"""
    try:
        # Chat history'yi hazırla
        messages = []
        for msg in chat_request.chat_history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Yeni kullanıcı mesajını ekle
        messages.append({"role": "user", "content": chat_request.message})
        
        # bot.py'deki query_chatbot fonksiyonunu kullan
        output = query_chatbot(messages)
        
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
    """Basit chat endpoint'i - bot.py'deki query_chatbot fonksiyonunu kullanır"""
    try:
        message = message_data.get("message", "")
        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # bot.py'deki query_chatbot fonksiyonunu kullan
        messages = [{"role": "user", "content": message}]
        output = query_chatbot(messages)
        
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