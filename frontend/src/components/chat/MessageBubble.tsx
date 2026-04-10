'use client';

import { ChatMessage } from '@/src/types/chat';

interface MessageBubbleProps {
  message: ChatMessage;
  isLatest?: boolean;
}

export default function MessageBubble({ message, isLatest }: MessageBubbleProps) {
  const timestamp = new Date(message.timestamp);
  const timeString = timestamp.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  // System messages
  if (message.role === 'system') {
    return (
      <div className="flex justify-center my-4 msg-system-enter">
        <div className="max-w-[85%] text-center">
          <div className="inline-flex items-center gap-2 text-[0.8125rem] text-gray-500 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-full border border-gray-200/50 shadow-sm font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400/60" />
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  const isUser = message.role === 'user';
  const isValidation = message.isValidationFeedback;

  return (
    <div
      className={`flex items-end gap-2 sm:gap-2.5 ${isUser ? 'justify-end' : 'justify-start'} ${
        isLatest ? (isUser ? 'msg-user-enter' : 'msg-bot-enter') : 'animate-fade-in'
      }`}
    >
      {/* Bot Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-500 via-teal-600 to-teal-600 flex items-center justify-center flex-shrink-0 mb-0.5 shadow-md shadow-teal-200/40 avatar-glow">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
            <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7Z" />
            <path d="M10 21h4" />
            <path d="M12 6v4" />
            <path d="M10 10h4" />
          </svg>
        </div>
      )}

      <div
        className={`max-w-[78%] sm:max-w-[72%] group relative ${
          isUser
            ? 'bg-gradient-to-br from-teal-500 via-teal-500 to-teal-600 text-white rounded-2xl rounded-br-md shadow-lg shadow-teal-200/30'
            : isValidation
            ? 'bg-gradient-to-br from-amber-50 to-orange-50 text-amber-900 border border-amber-200/80 rounded-2xl rounded-bl-md shadow-sm animate-gentle-shake'
            : 'bg-white text-gray-800 border border-gray-100 rounded-2xl rounded-bl-md shadow-sm hover:shadow-md transition-shadow duration-300'
        }`}
      >
        {/* Subtle inner glow for bot messages */}
        {!isUser && !isValidation && (
          <div className="absolute inset-0 rounded-2xl rounded-bl-md bg-gradient-to-br from-teal-50/30 via-transparent to-teal-50/20 pointer-events-none" />
        )}

        <div className="relative px-4 py-3">
          {/* Validation icon */}
          {isValidation && (
            <div className="flex items-center gap-1.5 mb-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 text-amber-500">
                <path fillRule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a.75.75 0 0 0 0 1.5h.253a.25.25 0 0 1 .244.304l-.459 2.066A1.75 1.75 0 0 0 10.747 15H11a.75.75 0 0 0 0-1.5h-.253a.25.25 0 0 1-.244-.304l.459-2.066A1.75 1.75 0 0 0 9.253 9H9Z" clipRule="evenodd" />
              </svg>
              <span className="text-[0.625rem] font-bold uppercase tracking-wider text-amber-500/80">More detail needed</span>
            </div>
          )}

          <p className={`whitespace-pre-wrap text-[0.875rem] sm:text-[0.9375rem] leading-relaxed ${
            isUser ? 'text-white/95' : ''
          }`}>
            {message.content}
          </p>

          <div className={`flex items-center gap-1.5 mt-1.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <p className={`text-[0.625rem] font-medium ${
              isUser ? 'text-teal-200/60' : isValidation ? 'text-amber-400/70' : 'text-gray-300'
            }`}>
              {timeString}
            </p>
            {/* Sent indicator for user messages */}
            {isUser && (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3 text-teal-200/50">
                <path fillRule="evenodd" d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z" clipRule="evenodd" />
              </svg>
            )}
          </div>
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-gray-600 to-gray-700 flex items-center justify-center flex-shrink-0 mb-0.5 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" className="w-4 h-4 opacity-90">
            <path fillRule="evenodd" d="M7.5 6a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0ZM3.751 20.105a8.25 8.25 0 0 1 16.498 0 .75.75 0 0 1-.437.695A18.683 18.683 0 0 1 12 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 0 1-.437-.695Z" clipRule="evenodd" />
          </svg>
        </div>
      )}
    </div>
  );
}
