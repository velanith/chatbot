'use client';

import { useState, FormEvent, useEffect } from 'react';
import { Message } from '../types';
import Sidebar from '../components/Sidebar';
import Chat from '../components/Chat';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: Message = { text: inputValue, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/simple', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: currentInput }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const botMessage: Message = { text: data.response, sender: 'bot' };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      // Hata durumunda varsayılan mesaj
      const errorMessage: Message = { 
        text: "Sorry, I couldn't process your request. Please try again.", 
        sender: 'bot' 
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
    </div>
  );
}