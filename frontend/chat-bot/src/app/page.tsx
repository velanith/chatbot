"use client";
import { useState, FormEvent, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import Chat from "../components/Chat";

interface Message {
  text: string;
  sender: "user" | "bot";
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [theme, setTheme] = useState("light");
  const [sessionId, setSessionId] = useState<string | null>(null); // ✅ İlk başta null

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      text: inputValue,
      sender: "user",
    };
    setMessages((prev) => [...prev, userMessage]);

    const currentInput = inputValue;
    setInputValue("");

    try {
      const response = await fetch("http://localhost:8000/api/v1/chat/memory", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          role: "user",
          content: currentInput,
          // ✅ İlk mesajda sessionId null, backend yeni session oluşturur
          ...(sessionId && { session_id: sessionId }),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Backend response:", data);

      // ✅ Backend'den gelen session_id'yi kaydet
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
        console.log("Session ID kaydedildi:", data.session_id);
      }

      const botMessage: Message = {
        text: data.content,
        sender: "bot",
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error:", error);

      const errorMessage: Message = {
        text: "Sorry, I couldn't process your request. Please try again.",
        sender: "bot",
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  return (
    <div className="container">
      <Sidebar theme={theme} setTheme={setTheme} />
      <Chat
        messages={messages}
        inputValue={inputValue}
        setInputValue={setInputValue}
        handleSubmit={handleSubmit}
      />
      {/* Debug için session ID'yi göster */}
      <div
        style={{
          position: "fixed",
          bottom: 0,
          left: 0,
          background: "black",
          color: "white",
          padding: "5px",
          fontSize: "10px",
        }}
      >
        Session: {sessionId || "Henüz oluşturulmadı"}
      </div>
    </div>
  );
}
