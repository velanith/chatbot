import json
import os
from datetime import datetime
from typing import Dict, List
from .bot import GPTOSSChatbot


class SessionMemoryChatbot(GPTOSSChatbot):
    def __init__(self, sessions_dir: str = "chat_sessions"):
        super().__init__()
        self.sessions_dir = sessions_dir
        self.current_session_id = None
        # Ana bot.py'den system prompt'u al
        self.default_system_prompt = self.get_default_system_prompt()
        self.ensure_sessions_dir()

    def get_default_system_prompt(self):
        """Bot.py'deki load_conversation fonksiyonundan varsayılan system prompt'u al"""
        # Bu method parent class'ın load_conversation methodunu kullanır
        conversation = super().load_conversation()

        # System message'ı bul
        for message in conversation:
            if message.get("role") == "system":
                return message.get("content")

        # Eğer bulunamazsa sabit bir prompt döndür
        return """Sen profesyonel bir dil öğrenme asistanısın. Ana görevin kullanıcıların İngilizce seviyelerini değerlendirmek ve onlara uygun pratik imkanları sunmak.
	       İLk OTURUM İÇİN SÜREÇ:
	      . 5 soruluk seviye belirleme testini uygula:
	        - Soru 1: Temel kelime bilgisi (A1 seviye) - Örnek: "What is your name?" gibi basit sorular
	        - Soru 2: Basit gramer yapıları (A2 seviye) - Örnek: "Complete: I ___ to school every day" (go/goes)
	        - Soru 3: Orta seviye anlama (B1 seviye) - Örnek: Kısa bir paragraf verip anlamı sor
	        - Soru 4: Karmaşık cümle kurma (B2 seviye) - Örnek: "If you had more time, what would you do?"
	        - Soru 5: İleri seviye ifadeler (C1 seviye) - Örnek: İdiyom veya karmaşık gramer yapıları
	      
	       TEST KURALLARI:
	       Her soruyu tek tek sor, kullanıcı cevap verene kadar bekle
	       Soruları sırayla ver, hepsini birden verme
	       Her cevaptan sonra "Teşekkürler, bir sonraki soru..." de, doğru cevabı verme
	       Test sırasında kullanıcıyı yönlendirme, sadece soruları sor
	      
	       TEST SONRASI DEĞERLENDİRME:
	       5 sorudan kaç tanesini doğru yaptığına göre seviye belirle:
	       * 0-1 doğru: A1 (Başlangıç)
	       * 2 doğru: A2 (Temel)
	       * 3 doğru: B1 (Orta)
	       * 4 doğru: B2 (Üst-Orta)
	       * 5 doğru: C1 (İleri)
	       Detaylı geri bildirim ver
	       Seviyesine uygun pratik önerileri sun
	      
	       DEVAM EDEN OTURUMLARDA:
	       Kullanıcının seviyesini hatırla
	       Konuşma pratiği, kelime oyunları, gramer egzersizleri sun
	       İlerlemesini takip et ve motive et
	      
	       GENEL KURALLAR:
	       Her zaman Türkçe konuş
	       Destekleyici ve sabırlı ol
	       Hataları düzeltirken kibar ol
	       Kullanıcının öğrenme hızına uyum sağla"""

    def ensure_sessions_dir(self):
        """Sessions klasörünü oluştur"""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
            print(f"📁 {self.sessions_dir} klasörü oluşturuldu.")

    def get_session_file(self, session_id: str) -> str:
        """Session dosyasının yolunu döndür"""
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def create_new_session(self) -> str:
        """Yeni session oluştur - varsayılan system prompt ile"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session_id = session_id

        # System prompt ile başla
        initial_messages = [
            {
                "role": "system",
                "content": self.default_system_prompt,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        # Session dosyası oluştur
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": initial_messages,
        }

        try:
            with open(self.get_session_file(session_id), "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)

            # Chat history'yi system prompt ile başlat
            self.chat_history = initial_messages.copy()

            print(f"✅ Yeni session oluşturuldu: {session_id}")
            print("🤖 System prompt yüklendi - Dil seviye testi için hazır!")
            return session_id

        except Exception as e:
            print(f"❌ Session oluşturma hatası: {e}")
            return None

    def load_session(self, session_id: str) -> bool:
        """Mevcut session'ı yükle"""
        session_file = self.get_session_file(session_id)

        if not os.path.exists(session_file):
            print(f"❌ Session bulunamadı: {session_id}")
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            self.current_session_id = session_id
            messages = session_data.get("messages", [])

            # Eğer session'da system prompt yoksa ekle
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                system_message = {
                    "role": "system",
                    "content": self.default_system_prompt,
                    "timestamp": datetime.now().isoformat(),
                }
                messages.insert(0, system_message)
                print("🔧 Session'a system prompt eklendi")

            self.chat_history = messages

            user_msg_count = len([m for m in messages if m.get("role") == "user"])
            print(
                f"✅ Session yüklendi: {session_id} ({user_msg_count} kullanıcı mesajı)"
            )
            return True

        except Exception as e:
            print(f"❌ Session yüklenirken hata: {e}")
            return False

    def save_session(self):
        """Mevcut session'ı kaydet"""
        if not self.current_session_id:
            print("❌ Aktif session yok!")
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

            return True

        except Exception as e:
            print(f"❌ Session kaydetme hatası: {e}")
            return False

    def list_sessions(self) -> List[Dict]:
        """Tüm session'ları listele"""
        sessions = []

        if not os.path.exists(self.sessions_dir):
            return sessions

        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                session_id = filename[:-5]  # .json uzantısını çıkar
                session_file = self.get_session_file(session_id)

                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)

                    # Son mesajı al (system mesajları hariç)
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

                    sessions.append(
                        {
                            "session_id": session_id,
                            "created_at": session_data.get("created_at"),
                            "message_count": len(
                                user_messages
                            ),  # System mesajları sayma
                            "last_message": last_message,
                        }
                    )

                except Exception as e:
                    print(f"❌ {filename} okunamadı: {e}")

        # En yeniden eskiye sırala
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return sessions

    def send_message_with_memory(self, message: str) -> str:
        """Memory ile mesaj gönder"""
        if not self.current_session_id:
            print("🆕 Session yok, yeni session oluşturuluyor...")
            self.create_new_session()

        # Kullanıcı mesajını ekle
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
        }
        self.chat_history.append(user_message)

        try:
            # Chat history uzunluğunu kontrol et (system prompt'u koru)
            max_messages = 41  # 40 mesaj + 1 system prompt
            if len(self.chat_history) > max_messages:
                # System prompt'u koru, en eski kullanıcı mesajlarını çıkar
                system_messages = [
                    m for m in self.chat_history if m.get("role") == "system"
                ]
                other_messages = [
                    m for m in self.chat_history if m.get("role") != "system"
                ]
                other_messages = other_messages[
                    -(max_messages - 1) :
                ]  # Son 40 mesajı al
                self.chat_history = system_messages + other_messages
                print(
                    f"📝 Chat history {max_messages} mesajla sınırlandı (system prompt korundu)"
                )

            # API için mesajları hazırla
            api_messages = []
            for msg in self.chat_history:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

            # API'ye gönder
            output = self.query_chatbot(api_messages)

            if "choices" in output and len(output["choices"]) > 0:
                bot_response = output["choices"][0]["message"]["content"]

                # Bot yanıtını ekle
                bot_message = {
                    "role": "assistant",
                    "content": bot_response,
                    "timestamp": datetime.now().isoformat(),
                }
                self.chat_history.append(bot_message)

                # Session'ı kaydet
                self.save_session()

                return bot_response
            else:
                return "❌ Bot'tan yanıt alınamadı"

        except Exception as e:
            # Hata durumunda son kullanıcı mesajını çıkar
            if self.chat_history and self.chat_history[-1]["role"] == "user":
                self.chat_history.pop()
            raise e

    def show_session_info(self):
        """Mevcut session bilgilerini göster"""
        if not self.current_session_id:
            print("❌ Aktif session yok")
            return

        user_messages = [
            m for m in self.chat_history if m.get("role") in ["user", "assistant"]
        ]
        has_system = any(m.get("role") == "system" for m in self.chat_history)

        print(f"\n📊 Session Bilgileri:")
        print(f"  Session ID: {self.current_session_id}")
        print(f"  Kullanıcı Mesajları: {len(user_messages)}")
        print(f"  System Prompt: {'✅ Var' if has_system else '❌ Yok'}")

        if user_messages:
            first_msg = user_messages[0]
            last_msg = user_messages[-1]
            print(f"  İlk Mesaj: {first_msg.get('timestamp', 'Bilinmiyor')}")
            print(f"  Son Mesaj: {last_msg.get('timestamp', 'Bilinmiyor')}")

    def reset_session_with_system_prompt(self):
        """Mevcut session'ı system prompt ile sıfırla"""
        if not self.current_session_id:
            print("❌ Aktif session yok")
            return False

        # Sadece system prompt'u koru
        system_message = {
            "role": "system",
            "content": self.default_system_prompt,
            "timestamp": datetime.now().isoformat(),
        }

        self.chat_history = [system_message]
        self.save_session()

        print("🔄 Session sıfırlandı - System prompt korundu")
        print("🤖 Dil seviye testi için hazır!")
        return True

    def export_session(self, session_id: str = None) -> str:
        """Session'ı metin dosyası olarak export et"""
        target_session = session_id or self.current_session_id

        if not target_session:
            return "❌ Export edilecek session yok"

        session_file = self.get_session_file(target_session)
        if not os.path.exists(session_file):
            return "❌ Session dosyası bulunamadı"

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            # Metin dosyası oluştur
            export_filename = f"{target_session}_export.txt"
            export_path = os.path.join(self.sessions_dir, export_filename)

            with open(export_path, "w", encoding="utf-8") as f:
                f.write(f"Sohbet Export - {target_session}\n")
                f.write(
                    f"Oluşturulma Tarihi: {session_data.get('created_at', 'Bilinmiyor')}\n"
                )

                messages = session_data.get("messages", [])
                user_messages = [
                    m for m in messages if m.get("role") in ["user", "assistant"]
                ]

                f.write(f"Toplam Mesaj: {len(user_messages)}\n")
                f.write("=" * 50 + "\n\n")

                # System prompt'u ayrı göster
                system_msg = next(
                    (m for m in messages if m.get("role") == "system"), None
                )
                if system_msg:
                    f.write("🤖 SYSTEM PROMPT:\n")
                    f.write(f"   {system_msg['content']}\n")
                    f.write("=" * 50 + "\n\n")

                # Kullanıcı mesajlarını göster
                counter = 1
                for msg in messages:
                    if msg.get("role") in ["user", "assistant"]:
                        role_name = "SEN" if msg["role"] == "user" else "GPT-OSS"
                        timestamp = msg.get("timestamp", "Bilinmiyor")
                        f.write(f"{counter:3d}. [{timestamp}] {role_name}:\n")
                        f.write(f"     {msg['content']}\n\n")
                        counter += 1

            return f"✅ Session export edildi: {export_path}"

        except Exception as e:
            return f"❌ Export hatası: {e}"
