'use client';

import { useEffect, useRef, useState } from 'react';
import { ChatMessage, McqOption } from '@/src/types/chat';

interface MessageBubbleProps {
  message: ChatMessage;
  isLatest?: boolean;
  // Edit support — only enabled on the last user message of an active session.
  canEdit?: boolean;
  onEditSubmit?: (
    messageId: string,
    content: string,
    resolvedOption: string | null,
  ) => Promise<{ ok: boolean; error?: string }>;
}

export default function MessageBubble({
  message,
  isLatest,
  canEdit,
  onEditSubmit,
}: MessageBubbleProps) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(message.content);
  const [picked, setPicked] = useState<string | null>(
    message.resolvedOption ?? null,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing) {
      setText(message.content);
      setPicked(message.resolvedOption ?? null);
      setError(null);
      requestAnimationFrame(() => textareaRef.current?.focus());
    }
  }, [editing, message.content, message.resolvedOption]);

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
  const options: McqOption[] | null | undefined = message.questionOptions;

  const startEdit = () => {
    if (!canEdit || busy) return;
    setEditing(true);
  };

  const cancelEdit = () => {
    if (busy) return;
    setEditing(false);
    setText(message.content);
    setPicked(message.resolvedOption ?? null);
    setError(null);
  };

  const submitEdit = async () => {
    if (!onEditSubmit || busy) return;
    const finalText = text.trim();
    if (!finalText && !picked) {
      setError('Answer cannot be empty');
      return;
    }
    setBusy(true);
    setError(null);
    const res = await onEditSubmit(message.id, finalText, picked);
    setBusy(false);
    if (res.ok) {
      setEditing(false);
    } else {
      setError(res.error || 'Could not save. Try again.');
    }
  };

  return (
    <div
      className={`flex items-end gap-2 sm:gap-2.5 ${isUser ? 'justify-end' : 'justify-start'} ${
        isLatest ? (isUser ? 'msg-user-enter' : 'msg-bot-enter') : 'animate-fade-in'
      }`}
    >
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
        {!isUser && !isValidation && (
          <div className="absolute inset-0 rounded-2xl rounded-bl-md bg-gradient-to-br from-teal-50/30 via-transparent to-teal-50/20 pointer-events-none" />
        )}

        <div className="relative px-4 py-3">
          {isValidation && (
            <div className="flex items-center gap-1.5 mb-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 text-amber-500">
                <path fillRule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a.75.75 0 0 0 0 1.5h.253a.25.25 0 0 1 .244.304l-.459 2.066A1.75 1.75 0 0 0 10.747 15H11a.75.75 0 0 0 0-1.5h-.253a.25.25 0 0 1-.244-.304l.459-2.066A1.75 1.75 0 0 0 9.253 9H9Z" clipRule="evenodd" />
              </svg>
              <span className="text-[0.625rem] font-bold uppercase tracking-wider text-amber-500/80">More detail needed</span>
            </div>
          )}

          {editing ? (
            <div className="space-y-2 min-w-[240px]">
              <textarea
                ref={textareaRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={2}
                disabled={busy}
                className="w-full text-[0.9375rem] leading-relaxed bg-white/90 text-gray-800 border border-white/40 rounded-lg px-2.5 py-2 outline-none focus:border-white/80 resize-none disabled:opacity-60"
              />
              {options && options.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {options.map((opt) => {
                    const selected = picked === opt.value;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setPicked(selected ? null : opt.value)}
                        disabled={busy}
                        className={`px-2 py-1 rounded-md text-[0.6875rem] font-medium border transition-colors ${
                          selected
                            ? 'bg-white text-teal-700 border-white'
                            : 'bg-white/10 text-white border-white/30 hover:bg-white/20'
                        } disabled:opacity-50`}
                      >
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
              )}
              {error && (
                <p className="text-[0.6875rem] text-red-100 bg-red-500/30 border border-red-200/40 rounded px-2 py-1">
                  {error}
                </p>
              )}
              <div className="flex items-center justify-end gap-1.5">
                <button
                  type="button"
                  onClick={cancelEdit}
                  disabled={busy}
                  className="px-2.5 py-1 text-[0.6875rem] font-semibold rounded-md bg-white/10 text-white border border-white/30 hover:bg-white/20 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={submitEdit}
                  disabled={busy}
                  className="px-2.5 py-1 text-[0.6875rem] font-semibold rounded-md bg-white text-teal-700 hover:bg-teal-50 disabled:opacity-50 inline-flex items-center gap-1"
                >
                  {busy && (
                    <span className="w-3 h-3 border-2 border-teal-400 border-t-teal-700 rounded-full animate-spin" />
                  )}
                  {busy ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className={`whitespace-pre-wrap text-[0.875rem] sm:text-[0.9375rem] leading-relaxed ${
                isUser ? 'text-white/95' : ''
              }`}>
                {message.content}
              </p>

              <div className={`flex items-center gap-1.5 mt-1.5 ${isUser ? 'justify-end' : 'justify-start'}`}>
                {isUser && message.editedAt && (
                  <span className="text-[0.625rem] font-medium text-teal-200/70 italic">edited</span>
                )}
                <p className={`text-[0.625rem] font-medium ${
                  isUser ? 'text-teal-200/60' : isValidation ? 'text-amber-400/70' : 'text-gray-300'
                }`}>
                  {timeString}
                </p>
                {isUser && (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3 text-teal-200/50">
                    <path fillRule="evenodd" d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z" clipRule="evenodd" />
                  </svg>
                )}
                {isUser && canEdit && (
                  <button
                    type="button"
                    onClick={startEdit}
                    aria-label="Edit this answer"
                    title="Edit this answer"
                    className="ml-1 text-teal-100/70 hover:text-white"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                      <path d="M2.695 14.763l-1.262 3.154a.5.5 0 00.65.65l3.155-1.262a4 4 0 001.343-.886L17.5 5.5a2.121 2.121 0 00-3-3L3.58 13.42a4 4 0 00-.885 1.343z" />
                    </svg>
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>

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
