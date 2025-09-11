import { FormEvent } from 'react';
import { Message } from '../types';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import Welcome from './Welcome';

type ChatProps = {
  messages: Message[];
  inputValue: string;
  setInputValue: (value: string) => void;
  handleSubmit: (e: FormEvent) => void;
};

export default function Chat({ messages, inputValue, setInputValue, handleSubmit }: ChatProps) {
  return (
    <main className="main-chat">
      <div className="chat-messages">
        {messages.length === 0 ? (
          <Welcome />
        ) : (
          messages.map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))
        )}
      </div>
      <ChatInput 
        inputValue={inputValue} 
        setInputValue={setInputValue} 
        handleSubmit={handleSubmit} 
      />
    </main>
  );
}
