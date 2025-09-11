import ThemeToggle from './ThemeToggle';

type SidebarProps = {
  theme: string;
  setTheme: (theme: string) => void;
};

export default function Sidebar({ theme, setTheme }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="new-chat-button">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        New Chat
      </div>
      <div className="chat-history">
        {/* Chat history items will be rendered here */}
      </div>
      <div className="user-settings">
        <div className="user-avatar">U</div>
        <span>User</span>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>
    </aside>
  );
}
