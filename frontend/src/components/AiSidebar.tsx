"use client";

import { useState, useRef, useEffect } from "react";
import type { BoardData } from "@/lib/kanban";

interface Message {
  role: "user" | "ai";
  content: string;
}

interface AiSidebarProps {
  onBoardUpdated: (newBoard: BoardData) => void;
}

export function AiSidebar({ onBoardUpdated }: AiSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", content: "Hi! I'm your Kanban AI assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
      });

      if (!res.ok) throw new Error("Failed to reach AI");

      const data = await res.json();
      setMessages(prev => [...prev, { role: "ai", content: data.response_message }]);
      
      if (data.updated_board) {
        onBoardUpdated(data.updated_board);
      }
    } catch (err: any) {
      setMessages(prev => [...prev, { role: "ai", content: "Sorry, I ran into an error processing your request." }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 rounded-full bg-[var(--primary-blue)] p-4 text-white shadow-lg transition hover:bg-[var(--navy-dark)]"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/>
        </svg>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex h-[500px] w-80 flex-col overflow-hidden rounded-2xl border border-[var(--stroke)] bg-white shadow-2xl">
      <div className="flex items-center justify-between border-b border-[var(--stroke)] bg-[var(--navy-dark)] px-4 py-3 text-white">
        <h3 className="font-semibold text-sm tracking-wider uppercase">AI Assistant</h3>
        <button onClick={() => setIsOpen(false)} className="text-white hover:text-gray-300">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 bg-[var(--surface)]">
        <div className="flex flex-col gap-3">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${msg.role === 'user' ? 'bg-[var(--primary-blue)] text-white' : 'bg-white border border-[var(--stroke)] text-[var(--navy-dark)]'}`}>
                {msg.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-[var(--stroke)] text-[var(--gray-text)] rounded-2xl px-4 py-2 text-sm animate-pulse">
                Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="border-t border-[var(--stroke)] bg-white p-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me to move a card..."
            className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm focus:border-[var(--primary-blue)] focus:outline-none focus:ring-1 focus:ring-[var(--primary-blue)]"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-xl bg-[var(--accent-yellow)] p-2 text-[var(--navy-dark)] transition hover:opacity-80 disabled:opacity-50"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
