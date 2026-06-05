'use client';

import { useMemo, useRef, useEffect } from 'react';
import { ChatMessage } from '@/src/types/chat';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

interface MessageListProps {
  messages: ChatMessage[];
  isTyping: boolean;
  canEditLastAnswer?: boolean;
  onEditSubmit?: (
    messageId: string,
    content: string,
    resolvedOption: string | null,
  ) => Promise<{ ok: boolean; error?: string }>;
}

export default function MessageList({
  messages,
  isTyping,
  canEditLastAnswer,
  onEditSubmit,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastBotRef = useRef<HTMLDivElement>(null);

  const lastUserMessageId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user') return messages[i].id;
    }
    return null;
  }, [messages]);

  const lastBotMessageId = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'bot') return messages[i].id;
    }
    return null;
  }, [messages]);

  // When the most-recent message is a BOT question, align its TOP to the top
  // of the scroll viewport so the full question is readable from the first
  // line down (long questions were previously scrolled so their top was
  // pushed above the fold / behind the sticky header). Otherwise (a user
  // answer just sent, or the typing indicator) keep the conversation pinned
  // to the bottom.
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    const showFromTop = !isTyping && lastMessage?.role === 'bot' && lastBotRef.current;
    if (showFromTop && lastBotRef.current) {
      lastBotRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages, isTyping]);

  return (
    <div
      className="flex-1 overflow-y-auto px-3 py-3 sm:px-6 sm:py-6 chat-scrollbar chat-bg-pattern relative flex flex-col"
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

      <div className="max-w-3xl mx-auto w-full space-y-4 relative mt-auto">
        {messages.map((message, index) => {
          const isLatestUser = message.id === lastUserMessageId;
          const isLatestBot = message.id === lastBotMessageId;
          const bubble = (
            <MessageBubble
              key={message.id}
              message={message}
              isLatest={index === messages.length - 1}
              canEdit={Boolean(canEditLastAnswer && isLatestUser)}
              onEditSubmit={onEditSubmit}
            />
          );
          // Wrap the latest bot message in a scroll-target with a top margin
          // that clears the sticky header so the question's first line is
          // always visible.
          if (isLatestBot) {
            return (
              <div key={message.id} ref={lastBotRef} style={{ scrollMarginTop: '12px' }}>
                {bubble}
              </div>
            );
          }
          return bubble;
        })}

        {isTyping && <TypingIndicator />}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
