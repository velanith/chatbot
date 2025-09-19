import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GPTOSSChatbot:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "GPT-OSS Chatbot",
        }
        # Konuşma geçmişini başlat
        self.conversation = self.load_conversation()

    def load_conversation(self):
        try:
            with open("conversation.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                {
                    "role": "system",
                    "content": """Sen profesyonel bir dil öğrenme asistanısın. Ana görevin kullanıcıların öğrenmek istedikleri yabancı dil seviyelerini değerlendirmek ve onlara uygun pratik imkanları sunmak.

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
- Kullanıcının öğrenme hızına uyum sağla""",
                }
            ]

    def save_conversation(self):
        """Mevcut konuşmayı JSON dosyasına kaydet"""
        with open("conversation.json", "w", encoding="utf-8") as f:
            json.dump(self.conversation, f, ensure_ascii=False, indent=2)

    def query_chatbot(self, messages):
        payload = {
            "model": "gpt-oss-20b",
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
            "stream": False,
        }

        try:
            response = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=50
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code != 200:
                print(f"Error Response: {response.text}")
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

    def test_connection(self):
        """API bağlantısını test et"""
        test_messages = [{"role": "user", "content": "Merhaba, nasılsın?"}]
        try:
            response = self.query_chatbot(test_messages)
            print("✅ API bağlantısı başarılı!")
            return True
        except Exception as e:
            print(f"❌ API bağlantı hatası: {e}")
            return False

    def clear_history(self):
        """Chat history'yi temizle"""
        # System message'ı koru, geri kalanını sil
        system_message = next(
            (msg for msg in self.conversation if msg["role"] == "system"), None
        )
        self.conversation = [system_message] if system_message else []
        self.save_conversation()
        print("📝 Sohbet geçmişi temizlendi!")

    def manage_conversation_length(self):
        """Konuşma uzunluğunu yönet (bellek tasarrufu için)"""
        # System message'ı koru
        system_msgs = [msg for msg in self.conversation if msg["role"] == "system"]
        other_msgs = [msg for msg in self.conversation if msg["role"] != "system"]

        # Son 20 mesajı tut (10 soru-cevap)
        if len(other_msgs) > 20:
            other_msgs = other_msgs[-20:]

        self.conversation = system_msgs + other_msgs

    def run(self):
        print("🚀 GPT-OSS Chatbot başlatıldı!")
        print("📋 Komutlar:")
        print("  • 'quit' veya 'exit' - Çıkış")
        print("  • 'clear' - Sohbet geçmişini temizle")
        print(
            f"📚 Mevcut konuşma: {len([m for m in self.conversation if m['role'] != 'system'])} mesaj"
        )
        print("-" * 50)

        while True:
            try:
                user_input = input("\n>> Sen: ").strip()

                # Çıkış komutları
                if user_input.lower() in ["quit", "exit", "çık"]:
                    print("👋 Görüşürüz!")
                    break

                # Özel komutlar
                if user_input.lower() == "clear":
                    self.clear_history()
                    continue

                # Boş girdi kontrolü
                if not user_input:
                    print("⚠️  Lütfen bir mesaj yazın.")
                    continue

                # Kullanıcı mesajını konuşmaya ekle
                self.conversation.append({"role": "user", "content": user_input})

                # Konuşma uzunluğunu yönet
                self.manage_conversation_length()

                print("🤖 Düşünüyor...")

                # TÜM konuşma geçmişini API'ye gönder
                output = self.query_chatbot(self.conversation)

                if "choices" in output and len(output["choices"]) > 0:
                    bot_response = output["choices"][0]["message"]["content"]
                    print(f"\n🤖 GPT-OSS: {bot_response}")

                    # Bot yanıtını da konuşmaya ekle
                    self.conversation.append(
                        {"role": "assistant", "content": bot_response}
                    )

                    # Konuşmayı kaydet
                    self.save_conversation()
                else:
                    print("❌ Bot'tan yanıt alınamadı")
                    # Başarısız durumda kullanıcı mesajını geri al
                    if self.conversation and self.conversation[-1]["role"] == "user":
                        self.conversation.pop()

            except KeyboardInterrupt:
                print("\n\n⏹️  Program sonlandırıldı.")
                break
            except Exception as e:
                print(f"❌ Hata: {e}")
                # Hata durumunda son kullanıcı mesajını geri al
                if self.conversation and self.conversation[-1]["role"] == "user":
                    self.conversation.pop()


def main():
    # Chatbot instance oluştur
    chatbot = GPTOSSChatbot()

    # API key kontrolü
    if not chatbot.api_key:
        print("❌ OPENROUTER_API_KEY bulunamadı! .env dosyanızı kontrol edin.")
        return

    print("🔑 API key bulundu, bağlantı test ediliyor...")

    # Bağlantı testi
    if chatbot.test_connection():
        chatbot.run()
    else:
        print("❌ API bağlantı testinde hata oluştu.")


if __name__ == "__main__":
    main()
