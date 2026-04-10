'use client';

import { useState, useCallback, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
  placeholder: string;
  validationFeedback?: string | null;
}

// Web Speech API types
interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getSpeechRecognition(): (new () => any) | null {
  if (typeof window === 'undefined') return null;
  return (
    (window as any).SpeechRecognition ||
    (window as any).webkitSpeechRecognition ||
    null
  );
}

function isMobile(): boolean {
  if (typeof navigator === 'undefined') return false;
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

export default function ChatInput({ onSend, disabled, placeholder, validationFeedback }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const recognitionRef = useRef<any>(null);
  // Accumulated final transcript from speech
  const accumulatedTextRef = useRef('');
  // Whether we intentionally want to keep listening (for auto-restart on mobile)
  const wantListeningRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setSpeechSupported(!!getSpeechRecognition());
  }, []);

  // Auto-resize textarea when value changes (handles speech input too)
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [value]);

  const startListening = useCallback(() => {
    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) return;

    // Store current text as the base before speech starts
    accumulatedTextRef.current = value;
    wantListeningRef.current = true;

    const mobile = isMobile();
    const recognition = new SpeechRecognition();
    // Mobile: use non-continuous mode + auto-restart to avoid duplication
    // Desktop: use continuous mode
    recognition.continuous = !mobile;
    recognition.interimResults = true;
    recognition.lang = 'en-GB';

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let sessionFinal = '';
      let sessionInterim = '';

      for (let i = 0; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          sessionFinal += transcript;
        } else {
          sessionInterim += transcript;
        }
      }

      // On mobile (non-continuous), each session is independent
      // sessionFinal is the complete final text from this recognition session
      // On desktop (continuous), we rebuild from all results each time
      const base = accumulatedTextRef.current;
      const separator = base.length > 0 && !base.endsWith(' ') ? ' ' : '';
      const newValue = (base + separator + sessionFinal + sessionInterim).trimStart();
      setValue(newValue);

      // When we get a final result on mobile, update the accumulated base
      // so the next auto-restart session doesn't repeat it
      if (mobile && sessionFinal) {
        accumulatedTextRef.current = (base + separator + sessionFinal).trimStart();
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        console.warn('Speech recognition error:', event.error);
      }
      // Don't stop listening state on 'no-speech' — let onend handle restart
      if (event.error !== 'no-speech') {
        wantListeningRef.current = false;
        setIsListening(false);
      }
    };

    recognition.onend = () => {
      // On mobile, auto-restart if user hasn't manually stopped
      if (mobile && wantListeningRef.current) {
        try {
          // Small delay to avoid rapid restart loops
          setTimeout(() => {
            if (wantListeningRef.current && recognitionRef.current) {
              recognitionRef.current.start();
            }
          }, 300);
          return; // Don't set isListening to false
        } catch {
          // If restart fails, fall through to stop
        }
      }
      wantListeningRef.current = false;
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [value]);

  const stopListening = useCallback(() => {
    wantListeningRef.current = false;
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // already stopped
      }
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  useEffect(() => {
    return () => {
      wantListeningRef.current = false;
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch { /* */ }
      }
    };
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      stopListening();
      const trimmed = value.trim();
      if (trimmed && !disabled) {
        onSend(trimmed);
        setValue('');
      }
    },
    [value, disabled, onSend, stopListening]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        stopListening();
        const trimmed = value.trim();
        if (trimmed && !disabled) {
          onSend(trimmed);
          setValue('');
        }
      }
    },
    [value, disabled, onSend, stopListening]
  );

  return (
    <div className="bg-white/95 backdrop-blur-md border-t border-gray-200/60 px-3 py-2 sm:px-6 sm:py-3 shadow-[0_-4px_20px_rgba(0,0,0,0.03)]">
      <div className="max-w-3xl mx-auto">
        {/* Validation feedback */}
        {validationFeedback && (
          <div className="mb-2 px-3 py-2 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/80 rounded-xl animate-slide-up">
            <p className="text-xs text-amber-700 flex items-center gap-2 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 flex-shrink-0 text-amber-500">
                <path fillRule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a.75.75 0 0 0 0 1.5h.253a.25.25 0 0 1 .244.304l-.459 2.066A1.75 1.75 0 0 0 10.747 15H11a.75.75 0 0 0 0-1.5h-.253a.25.25 0 0 1-.244-.304l.459-2.066A1.75 1.75 0 0 0 9.253 9H9Z" clipRule="evenodd" />
              </svg>
              Please provide more detail for a better assessment
            </p>
          </div>
        )}

        {/* Listening indicator */}
        {isListening && (
          <div className="mb-2 px-3 py-2 bg-gradient-to-r from-red-50 to-pink-50 border border-red-200/80 rounded-xl flex items-center gap-2.5 animate-slide-up">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
            <p className="text-xs text-red-700 font-semibold">Listening... speak now</p>
            <button
              type="button"
              onClick={stopListening}
              className="ml-auto text-[0.6875rem] text-red-600 font-bold hover:text-red-800 bg-red-100 hover:bg-red-200 px-2.5 py-1 rounded-lg transition-colors"
            >
              Stop
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-1.5 sm:gap-2.5 items-end">
          <div className="flex-1 relative min-w-0">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={placeholder}
              disabled={disabled}
              rows={1}
              aria-label="Type your message"
              className={`w-full min-h-[42px] sm:min-h-[46px] max-h-[120px] rounded-2xl px-3.5 sm:px-5 py-2.5 sm:py-3
                focus:outline-none
                disabled:opacity-50 disabled:cursor-not-allowed
                text-gray-800 placeholder-gray-400 text-sm
                resize-none
                transition-all duration-200
                ${isListening
                  ? 'border-2 border-red-300 bg-red-50/30 shadow-sm shadow-red-100/50'
                  : isFocused
                  ? 'border-2 border-teal-400 bg-white shadow-md shadow-teal-100/30'
                  : 'border-2 border-gray-200 bg-gray-50/50 hover:border-gray-300 hover:bg-white'
                }`}
              style={{ overflowY: 'auto' }}
            />
            {value.length > 0 && (
              <span className={`absolute right-3 bottom-1.5 text-[0.625rem] font-medium tabular-nums transition-colors ${
                value.length > 500 ? 'text-amber-500' : 'text-gray-300'
              }`}>
                {value.length}
              </span>
            )}
          </div>

          {/* Microphone button */}
          {speechSupported && (
            <button
              type="button"
              onClick={toggleListening}
              disabled={disabled}
              aria-label={isListening ? 'Stop listening' : 'Start voice input'}
              className={`h-[42px] w-[42px] sm:h-[46px] sm:w-[46px] flex items-center justify-center flex-shrink-0
                rounded-2xl transition-all duration-200
                ${isListening
                  ? 'bg-red-500 hover:bg-red-600 text-white shadow-lg shadow-red-200/50 animate-pulse'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-500 hover:text-gray-700 shadow-sm'
                }
                disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M8.25 4.5a3.75 3.75 0 1 1 7.5 0v8.25a3.75 3.75 0 1 1-7.5 0V4.5Z" />
                <path d="M6 10.5a.75.75 0 0 1 .75.75v1.5a5.25 5.25 0 1 0 10.5 0v-1.5a.75.75 0 0 1 1.5 0v1.5a6.751 6.751 0 0 1-6 6.709v2.291h3a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3v-2.291a6.751 6.751 0 0 1-6-6.709v-1.5A.75.75 0 0 1 6 10.5Z" />
              </svg>
            </button>
          )}

          {/* Send button */}
          <button
            type="submit"
            disabled={disabled || !value.trim()}
            aria-label="Send message"
            className={`h-[42px] w-[42px] sm:h-[46px] sm:w-[46px] flex items-center justify-center flex-shrink-0
              rounded-2xl
              transition-all duration-200
              focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus-visible:ring-offset-1
              ${value.trim() && !disabled
                ? 'bg-gradient-to-r from-teal-500 via-teal-600 to-teal-600 hover:from-teal-600 hover:via-teal-700 hover:to-teal-700 text-white shadow-lg shadow-teal-200/40 hover:shadow-xl hover:shadow-teal-200/50 hover:-translate-y-0.5 active:translate-y-0'
                : 'bg-gray-100 text-gray-300 cursor-not-allowed'
              }`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-5 h-5"
              aria-hidden="true"
            >
              <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
