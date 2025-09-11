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

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: Message = { text: inputValue, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    // Simulate bot response
    setTimeout(() => {
      const botMessage: Message = { text: "That's a great goal! What would you like to write about?", sender: 'bot' };
      setMessages((prev) => [...prev, botMessage]);
    }, 1000);
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