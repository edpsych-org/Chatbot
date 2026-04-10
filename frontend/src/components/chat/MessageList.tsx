'use client';

import { useRef, useEffect } from 'react';
import { ChatMessage } from '@/src/types/chat';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

interface MessageListProps {
  messages: ChatMessage[];
  isTyping: boolean;
}

export default function MessageList({ messages, isTyping }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  return (
    <div
      className="flex-1 overflow-y-auto px-3 py-5 sm:px-6 sm:py-8 chat-scrollbar chat-bg-pattern relative"
      role="log"
      aria-live="polite"
      aria-label="Chat messages"
    >
      {/* Decorative floating dots */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="floating-dot w-3 h-3" style={{ left: '10%', bottom: '20%', animationDuration: '15s', animationDelay: '0s' }} />
        <div className="floating-dot w-2 h-2" style={{ left: '70%', bottom: '10%', animationDuration: '20s', animationDelay: '5s' }} />
        <div className="floating-dot w-4 h-4" style={{ left: '85%', bottom: '30%', animationDuration: '18s', animationDelay: '2s' }} />
        <div className="floating-dot w-2.5 h-2.5" style={{ left: '30%', bottom: '5%', animationDuration: '22s', animationDelay: '8s' }} />
      </div>

      <div className="max-w-3xl mx-auto space-y-4 relative">
        {messages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            isLatest={index === messages.length - 1}
          />
        ))}

        {isTyping && <TypingIndicator />}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
