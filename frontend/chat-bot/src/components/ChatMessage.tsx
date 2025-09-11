import { Message } from '../types';

type ChatMessageProps = {
  message: Message;
};

export default function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div className={`message ${message.sender}`}>
      <div className="message-avatar">
        {message.sender === 'bot' ? (
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M12,2A10,10,0,0,0,2,12A10,10,0,0,0,12,22A10,10,0,0,0,22,12A10,10,0,0,0,12,2ZM8,12.5A1.5,1.5,0,1,1,9.5,11,1.5,1.5,0,0,1,8,12.5ZM14.5,14A1.5,1.5,0,1,1,16,12.5,1.5,1.5,0,0,1,14.5,14Z"/></svg>
        ) : (
          <div className="user-avatar-icon">U</div>
        )}
      </div>
      <div className="message-content">
        {message.text}
      </div>
    </div>
  );
}
