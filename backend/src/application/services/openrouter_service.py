"""OpenRouter API service for language learning chatbot."""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
from src.infrastructure.config import get_settings


class OpenRouterService:
    """OpenRouter API service for GPT-OSS model."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"OpenRouter API key configured: {bool(self.api_key and self.api_key.strip())}")
        if self.api_key:
            logger.info(f"API key starts with: {self.api_key[:10]}...")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.app_host,
            "X-Title": "Polyglot Language Learning",
        }
        
    def get_language_learning_system_prompt(self) -> str:
        """Get the system prompt for language learning."""
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

    async def query_chatbot(self, messages: List[Dict]) -> Dict:
        """Query the OpenRouter API with messages."""
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError("OPENROUTER_API_KEY not configured")
            
        payload = {
            "model": "gpt-oss-20b",
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
            "stream": False,
        }

        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                json=payload, 
                timeout=50
            )

            if response.status_code != 200:
                raise Exception(
                    f"API request failed with status {response.status_code}: {response.text}"
                )

            if not response.text.strip():
                raise Exception("Empty response from API")

            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response: {response.text[:200]}")

    async def test_connection(self) -> bool:
        """Test API connection."""
        test_messages = [{"role": "user", "content": "Merhaba, nasılsın?"}]
        try:
            await self.query_chatbot(test_messages)
            return True
        except Exception:
            return False

    async def send_message(self, messages: List[Dict]) -> str:
        """Send message and get response."""
        try:
            output = await self.query_chatbot(messages)
            
            if "choices" in output and len(output["choices"]) > 0:
                return output["choices"][0]["message"]["content"]
            else:
                raise Exception("No response from API")
                
        except Exception as e:
            raise Exception(f"Error sending message: {str(e)}")