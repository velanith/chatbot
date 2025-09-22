"""OpenRouter chatbot service implementation."""

import json
import os
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.infrastructure.logging import get_logger
from src.infrastructure.config import get_settings

logger = get_logger(__name__)


class OpenRouterChatbotService:
    """OpenRouter API ile chatbot servisi."""
    
    def __init__(self):
        """Initialize OpenRouter chatbot service."""
        self.settings = get_settings()
        self.api_key = self.settings.openrouter_api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Debug logging
        logger.info(f"OpenRouter chatbot API key configured: {bool(self.api_key and self.api_key.strip())}")
        if self.api_key:
            logger.info(f"API key starts with: {self.api_key[:10]}...")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.app_host,
            "X-Title": "Polyglot Language Learning",
        }
        self.default_model = "gpt-oss-20b"
        
    def get_system_prompt(self) -> str:
        """Get default system prompt for language learning."""
        return """Sen profesyonel bir dil öğrenme asistanısın. Ana görevin kullanıcıların öğrenmek istedikleri yabancı dil seviyelerini değerlendirmek ve onlara uygun pratik imkanları sunmak.

İLK OTURUM İÇİN SÜREÇ:
1. Kullanıcıya hoş geldin mesajı ver ve kendini tanıt
2. Hangi dilde pratik yapmak istediğini sor (varsayılan: İngilizce)
3. 5 soruluk seviye belirleme testini uygula:
   - Soru 1: Temel kelime bilgisi (A1 seviye) - Örnek: "What is your name?" gibi basit sorular
   - Soru 2: Basit gramer yapıları (A2 seviye) - Örnek: "Complete: I ___ to school every day" (go/goes)
   - Soru 3: Orta seviye anlama (B1 seviye) - Örnek: Kısa bir paragraf verip anlamı sor
   - Soru 4: Karmaşık cümle kurma (B2 seviye) - Örnek: "If you had more time, what would you do?"
   - Soru 5: İleri seviye ifadeler (C1 seviye) - Örnek: İdiyom veya karmaşık gramer yapıları

TEST KURALLARI:
- Her soruyu tek tek sor, kullanıcı cevap verene kadar bekle
- Soruları sırayla ver, hepsini birden verme
- Her cevaptan sonra "Teşekkürler, bir sonraki soru..." de, doğru cevabı verme
- Test sırasında kullanıcıyı yönlendirme, sadece soruları sor

TEST SONRASI DEĞERLENDİRME:
- 5 sorudan kaç tanesini doğru yaptığına göre seviye belirle:
  * 0-1 doğru: A1 (Başlangıç)
  * 2 doğru: A2 (Temel)
  * 3 doğru: B1 (Orta)
  * 4 doğru: B2 (Üst-Orta)
  * 5 doğru: C1 (İleri)
- Detaylı geri bildirim ver
- Seviyesine uygun pratik önerileri sun

DEVAM EDEN OTURUMLARDA:
- Kullanıcının seviyesini hatırla
- Konuşma pratiği, kelime oyunları, gramer egzersizleri sun
- İlerlemesini takip et ve motive et

GENEL KURALLAR:
- Her zaman Türkçe konuş
- Destekleyici ve sabırlı ol
- Hataları düzeltirken kibar ol
- Kullanıcının öğrenme hızına uyum sağla"""

    async def send_message(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Send message to OpenRouter API."""
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError("OpenRouter API key not configured")
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        
        try:
            logger.info(f"Sending request to OpenRouter API with {len(messages)} messages")
            
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload, 
                timeout=50
            )
            
            logger.info(f"OpenRouter API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.text}")
                raise Exception(
                    f"API request failed with status {response.status_code}: {response.text}"
                )
            
            if not response.text.strip():
                raise Exception("Empty response from API")
            
            result = response.json()
            logger.info("OpenRouter API request successful")
            return result
            
        except requests.exceptions.Timeout:
            logger.error("OpenRouter API request timed out")
            raise Exception("Request timed out")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise Exception(f"Request failed: {e}")
        except ValueError as e:
            logger.error(f"Invalid JSON response from OpenRouter API: {response.text[:200]}")
            raise Exception(f"Invalid JSON response: {response.text[:200]}")
    
    async def chat_completion(
        self, 
        user_message: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        include_system_prompt: bool = True
    ) -> str:
        """Get chat completion from OpenRouter."""
        messages = []
        
        # Add system prompt if requested
        if include_system_prompt:
            messages.append({
                "role": "system",
                "content": self.get_system_prompt()
            })
        
        # Add chat history
        if chat_history:
            messages.extend(chat_history)
        
        # Add user message
        messages.append({
            "role": "user", 
            "content": user_message
        })
        
        # Send to API
        response = await self.send_message(messages)
        
        # Extract response
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        else:
            raise Exception("No response from OpenRouter API")
    
    async def test_connection(self) -> bool:
        """Test OpenRouter API connection."""
        try:
            test_messages = [{"role": "user", "content": "Merhaba, nasılsın?"}]
            await self.send_message(test_messages)
            logger.info("OpenRouter API connection test successful")
            return True
        except Exception as e:
            logger.error(f"OpenRouter API connection test failed: {e}")
            return False