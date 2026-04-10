'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import {
  ChatMessage,
  McqOption,
  QuestionMetadata,
  BotResponse,
} from '@/src/types/chat';
import MessageList from './MessageList';
import McqOptions from './McqOptions';
import ChatInput from './ChatInput';
import ProgressBar from './ProgressBar';
import CompletionBanner from './CompletionBanner';
import ChatSkeleton from './ChatSkeleton';

import { API_BASE } from '@/lib/api';

const STORAGE_KEY_PREFIX = 'chat_session_';
const SLOW_RESPONSE_MS = 10_000;
const MAX_RETRIES = 2;

interface HybridChatProps {
  assignmentId: string;
}

interface PersistedSession {
  sessionId: string;
  progress: number;
}

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token') || localStorage.getItem('token');
}

function getStorageKey(assignmentId: string): string {
  return `${STORAGE_KEY_PREFIX}${assignmentId}`;
}

function loadPersistedSession(assignmentId: string): PersistedSession | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(getStorageKey(assignmentId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PersistedSession;
    if (parsed.sessionId) return parsed;
    return null;
  } catch {
    return null;
  }
}

function savePersistedSession(assignmentId: string, sessionId: string, progress: number): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(
      getStorageKey(assignmentId),
      JSON.stringify({ sessionId, progress })
    );
  } catch {
    // storage quota exceeded
  }
}

function clearPersistedSession(assignmentId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(getStorageKey(assignmentId));
}

export default function HybridChat({ assignmentId }: HybridChatProps) {
  const router = useRouter();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<QuestionMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [currentCategory, setCurrentCategory] = useState<string | undefined>(undefined);
  const [inputFeedback, setInputFeedback] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<{
    type: 'mcq_choice' | 'free_text';
    content: string;
    choiceValue?: string;
  } | null>(null);
  const [consecutiveMcqCount, setConsecutiveMcqCount] = useState(0);
  const [showTextNudge, setShowTextNudge] = useState(false);
  const nudgeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const slowTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
      if (nudgeTimerRef.current) clearTimeout(nudgeTimerRef.current);
    };
  }, []);

  const addSystemMessage = useCallback((content: string) => {
    const msg: ChatMessage = {
      id: `sys-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      role: 'system',
      message_type: 'system_message',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, msg]);
  }, []);

  const startSlowResponseTimer = useCallback(() => {
    if (slowTimerRef.current) clearTimeout(slowTimerRef.current);
    slowTimerRef.current = setTimeout(() => {
      if (mountedRef.current) {
        addSystemMessage('Taking a moment... please wait.');
      }
    }, SLOW_RESPONSE_MS);
  }, [addSystemMessage]);

  const clearSlowResponseTimer = useCallback(() => {
    if (slowTimerRef.current) {
      clearTimeout(slowTimerRef.current);
      slowTimerRef.current = null;
    }
  }, []);

  // Initialize session on mount
  useEffect(() => {
    let active = true;

    async function restoreExistingSession(existingSessionId: string): Promise<boolean> {
      try {
        const token = getAuthToken();
        if (!token) return false;

        const response = await axios.get(
          `${API_BASE}/hybrid-chat/sessions/${existingSessionId}`,
          { headers: { Authorization: `Bearer ${token}` }, timeout: 10000 }
        );

        if (!active) return false;

        const data = response.data;
        setSessionId(existingSessionId);

        if (data.messages && Array.isArray(data.messages)) {
          const restored: ChatMessage[] = data.messages.map(
            (m: Record<string, unknown>, idx: number) => ({
              id: (m.id as string) || `restored-${idx}`,
              role: m.role as ChatMessage['role'],
              message_type: (m.message_type as ChatMessage['message_type']) || 'text',
              content: m.content as string,
              metadata: m.metadata as QuestionMetadata | undefined,
              timestamp: (m.timestamp as string) || new Date().toISOString(),
            })
          );
          setMessages(restored);

          // Prefer current_question from backend (has options from flow engine)
          if (data.current_question?.metadata) {
            setCurrentQuestion(data.current_question.metadata as QuestionMetadata);
          } else {
            const lastBotWithMeta = [...restored]
              .reverse()
              .find((m) => m.role === 'bot' && m.metadata?.options);
            if (lastBotWithMeta?.metadata) {
              setCurrentQuestion(lastBotWithMeta.metadata);
            }
          }
        }

        setProgress(data.progress_percentage || 0);
        if (data.status === 'completed') setIsCompleted(true);

        return true;
      } catch {
        return false;
      }
    }

    async function createNewSession(): Promise<void> {
      try {
        const token = getAuthToken();
        if (!token) {
          addSystemMessage('Please log in to start the assessment.');
          return;
        }

        const response = await axios.post(
          `${API_BASE}/hybrid-chat/start`,
          { assignment_id: assignmentId, flow_type: 'parent_assessment_v1' },
          { headers: { Authorization: `Bearer ${token}` }, timeout: 15000 }
        );

        if (!active) return;

        const data = response.data;
        setSessionId(data.session_id);

        if (data.resumed && data.messages && Array.isArray(data.messages)) {
          // Existing session returned — restore messages like restoreExistingSession
          const restored: ChatMessage[] = data.messages.map(
            (m: Record<string, unknown>, idx: number) => ({
              id: (m.id as string) || `restored-${idx}`,
              role: m.role as ChatMessage['role'],
              message_type: (m.message_type as ChatMessage['message_type']) || 'text',
              content: m.content as string,
              metadata: m.metadata as QuestionMetadata | undefined,
              timestamp: (m.timestamp as string) || new Date().toISOString(),
            })
          );
          setMessages(restored);

          // Prefer current_question from backend (has options from flow engine)
          if (data.current_question?.metadata) {
            setCurrentQuestion(data.current_question.metadata as QuestionMetadata);
          } else {
            const lastBotWithMeta = [...restored]
              .reverse()
              .find((m) => m.role === 'bot' && m.metadata?.options);
            if (lastBotWithMeta?.metadata) {
              setCurrentQuestion(lastBotWithMeta.metadata);
            }
          }

          setProgress(data.progress_percentage || 0);
          if (data.status === 'completed') setIsCompleted(true);
          savePersistedSession(assignmentId, data.session_id, data.progress_percentage || 0);
        } else if (data.bot_message) {
          const botMessage: ChatMessage = {
            id: `bot-${Date.now()}`,
            role: 'bot',
            message_type: (data.bot_message.message_type || 'text') as ChatMessage['message_type'],
            content: data.bot_message.content,
            metadata: data.bot_message.metadata,
            timestamp: new Date().toISOString(),
          };
          setMessages([botMessage]);
          setCurrentQuestion(data.bot_message.metadata || null);
          savePersistedSession(assignmentId, data.session_id, 0);
        }
      } catch (err: unknown) {
        if (!active) return;
        // Check if the assessment is already completed
        if (axios.isAxiosError(err) && err.response?.status === 400 && err.response?.data?.detail?.includes('already been completed')) {
          setIsCompleted(true);
          addSystemMessage('This assessment has already been completed.');
          return;
        }
        addSystemMessage('Something went wrong. Please refresh the page to try again.');
      }
    }

    async function init() {
      try {
        const persisted = loadPersistedSession(assignmentId);

        if (persisted) {
          const restored = await restoreExistingSession(persisted.sessionId);
          if (!active) return;
          if (restored) return;
          clearPersistedSession(assignmentId);
        }

        if (!active) return;
        await createNewSession();
      } finally {
        if (active) {
          setInitializing(false);
        }
      }
    }

    init();
    return () => { active = false; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assignmentId]);

  const completeAssessment = useCallback(
    async (sid: string) => {
      try {
        const token = getAuthToken();
        await axios.post(
          `${API_BASE}/hybrid-chat/sessions/${sid}/complete`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } catch {
        // Non-critical
      }
      clearPersistedSession(assignmentId);
    },
    [assignmentId]
  );

  const sendMessage = useCallback(
    async (
      messageType: 'mcq_choice' | 'free_text',
      content: string,
      choiceValue?: string,
      retryAttempt: number = 0,
    ) => {
      if (!sessionId || loading) return;

      setLoading(true);
      setIsTyping(true);
      setInputFeedback(null);
      setLastFailedMessage(null);
      startSlowResponseTimer();

      // Add user message immediately (only on first attempt)
      if (retryAttempt === 0) {
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          role: 'user',
          message_type: messageType === 'mcq_choice' ? 'mcq_choice' : 'text',
          content,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);
      }

      try {
        const token = getAuthToken();
        const response = await axios.post(
          `${API_BASE}/hybrid-chat/sessions/${sessionId}/message`,
          {
            message_type: messageType,
            content,
            choice_value: choiceValue,
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        if (!mountedRef.current) return;
        clearSlowResponseTimer();

        const data: BotResponse = response.data;

        // Handle input validation feedback
        if (data.input_feedback) {
          setInputFeedback(data.input_feedback);
        }

        if (data.bot_message) {
          const isValidation = data.bot_message.metadata?.validation === true;
          const botMessage: ChatMessage = {
            id: `bot-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            role: 'bot',
            message_type: (data.bot_message.message_type || 'text') as ChatMessage['message_type'],
            content: data.bot_message.content,
            metadata: data.bot_message.metadata,
            timestamp: new Date().toISOString(),
            isValidationFeedback: isValidation,
          };
          setMessages((prev) => [...prev, botMessage]);
          setCurrentQuestion(data.bot_message.metadata || null);
        }

        const newProgress = data.progress_percentage || 0;
        setProgress(newProgress);

        if (data.current_category) {
          setCurrentCategory(data.current_category);
        }

        savePersistedSession(assignmentId, sessionId, newProgress);

        if (data.status === 'completed' || data.is_complete) {
          setIsCompleted(true);
          completeAssessment(sessionId);
        }
      } catch (err: unknown) {
        if (!mountedRef.current) return;
        clearSlowResponseTimer();

        // Check if assessment was already completed
        if (axios.isAxiosError(err) && err.response?.status === 400 && err.response?.data?.detail?.includes('already been completed')) {
          setIsCompleted(true);
          addSystemMessage('This assessment has already been completed.');
          return;
        }

        // Auto-retry on failure (up to MAX_RETRIES)
        if (retryAttempt < MAX_RETRIES) {
          setTimeout(() => {
            sendMessage(messageType, content, choiceValue, retryAttempt + 1);
          }, 1000 * (retryAttempt + 1));
          return;
        }

        // After all retries exhausted, show retry button
        setLastFailedMessage({ type: messageType, content, choiceValue });
        addSystemMessage(
          'Having trouble connecting. Please check your internet and try again.'
        );
      } finally {
        if (mountedRef.current && retryAttempt >= MAX_RETRIES || retryAttempt === 0) {
          // Only stop loading after final attempt or if no retry needed
        }
        if (mountedRef.current) {
          setLoading(false);
          setIsTyping(false);
        }
      }
    },
    [
      sessionId,
      loading,
      assignmentId,
      startSlowResponseTimer,
      clearSlowResponseTimer,
      completeAssessment,
      addSystemMessage,
    ]
  );

  const handleMcqSelect = useCallback(
    (option: McqOption) => {
      setInputFeedback(null);
      sendMessage('mcq_choice', option.label, option.value);
      setConsecutiveMcqCount((prev) => {
        const next = prev + 1;
        if (next >= 3 && next % 3 === 0) {
          setShowTextNudge(true);
          if (nudgeTimerRef.current) clearTimeout(nudgeTimerRef.current);
          nudgeTimerRef.current = setTimeout(() => setShowTextNudge(false), 6000);
        }
        return next;
      });
    },
    [sendMessage]
  );

  const handleTextSend = useCallback(
    (text: string) => {
      setInputFeedback(null);
      sendMessage('free_text', text);
      setConsecutiveMcqCount(0);
      setShowTextNudge(false);
      if (nudgeTimerRef.current) clearTimeout(nudgeTimerRef.current);
    },
    [sendMessage]
  );

  const handleRetry = useCallback(() => {
    if (lastFailedMessage) {
      sendMessage(
        lastFailedMessage.type,
        lastFailedMessage.content,
        lastFailedMessage.choiceValue
      );
    }
  }, [lastFailedMessage, sendMessage]);

  const handleNavigateDashboard = useCallback(() => {
    router.push('/dashboard');
  }, [router]);

  const handleSaveAndExit = useCallback(() => {
    // Session is already persisted to DB on every message, so just navigate away
    if (sessionId) {
      savePersistedSession(assignmentId, sessionId, progress);
    }
    router.push('/dashboard');
  }, [router, sessionId, assignmentId, progress]);

  if (initializing) {
    return <ChatSkeleton />;
  }

  const showTextInput =
    !isCompleted && (currentQuestion?.allow_text || !currentQuestion?.options);

  const inputPlaceholder = 'Type your answer...';

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-slate-50 via-gray-50 to-gray-100/80">
      {/* Sticky header + progress bar wrapper */}
      <div className="sticky top-0 z-30 flex-shrink-0">
      {/* Header */}
      <header className="relative bg-white/95 backdrop-blur-md border-b border-gray-200/60 px-3 py-2.5 sm:px-6 sm:py-3 shadow-[0_1px_4px_rgba(0,0,0,0.04)] overflow-hidden">
        {/* Subtle animated shine */}
        <div className="absolute inset-0 header-shine pointer-events-none" />

        <div className="max-w-3xl mx-auto flex items-center gap-2.5 sm:gap-3 relative">
          {/* Logo / Avatar */}
          <div className="relative group">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-teal-500 via-teal-600 to-teal-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-teal-200/40 group-hover:shadow-xl group-hover:shadow-teal-200/50 transition-shadow duration-300">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 sm:w-[22px] sm:h-[22px]">
                <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7Z" />
                <path d="M10 21h4" />
                <path d="M12 6v4" />
                <path d="M10 10h4" />
              </svg>
            </div>
            {/* Online indicator */}
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white shadow-sm" />
          </div>

          {/* Title */}
          <div className="flex-1 min-w-0">
            <h1 className="text-sm sm:text-base font-semibold text-gray-900 tracking-tight truncate">
              The EdPsych Practice Assessment
            </h1>
            <p className="text-[0.625rem] sm:text-xs text-gray-400 font-medium hidden sm:block">
              Educational Psychology - Confidential
            </p>
          </div>

          {/* Category badge */}
          {currentCategory && (
            <div className="hidden sm:flex items-center animate-fade-in">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.6875rem] font-semibold bg-gradient-to-r from-teal-50 to-teal-50 text-teal-600 ring-1 ring-teal-100/80 capitalize shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                {currentCategory}
              </span>
            </div>
          )}

          {/* Save & Exit */}
          {!isCompleted && (
            <button
              onClick={handleSaveAndExit}
              className="flex items-center gap-1.5 px-3 py-1.5 sm:px-4 sm:py-2
                bg-white border border-gray-200 hover:border-teal-200 hover:bg-teal-50/50
                text-gray-500 hover:text-teal-600
                text-xs sm:text-sm font-medium rounded-xl
                transition-all duration-200 shadow-sm hover:shadow"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 sm:w-4 sm:h-4">
                <path d="M3 3.5A1.5 1.5 0 0 1 4.5 2h6.879a1.5 1.5 0 0 1 1.06.44l4.122 4.12A1.5 1.5 0 0 1 17 7.622V16.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 3 16.5v-13Z" />
              </svg>
              <span className="hidden sm:inline">Save & Exit</span>
              <span className="sm:hidden">Save</span>
            </button>
          )}
        </div>
      </header>

      <ProgressBar percentage={progress} currentCategory={currentCategory} />
      </div>{/* end sticky wrapper */}

      {/* Encryption notice */}
      <div className="flex items-center justify-center gap-1.5 py-1.5 bg-amber-50/60 border-b border-amber-100/50">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3 text-amber-500">
          <path fillRule="evenodd" d="M8 1a3.5 3.5 0 0 0-3.5 3.5V7A1.5 1.5 0 0 0 3 8.5v5A1.5 1.5 0 0 0 4.5 15h7a1.5 1.5 0 0 0 1.5-1.5v-5A1.5 1.5 0 0 0 11.5 7V4.5A3.5 3.5 0 0 0 8 1Zm2 6V4.5a2 2 0 1 0-4 0V7h4Z" clipRule="evenodd" />
        </svg>
        <span className="text-[0.625rem] text-amber-600 font-medium">End-to-end encrypted - Your responses are confidential</span>
      </div>

      <MessageList messages={messages} isTyping={isTyping} />

      {/* Retry Button */}
      {lastFailedMessage && !loading && (
        <div className="px-4 py-2.5 bg-gradient-to-r from-amber-50 to-orange-50 backdrop-blur-sm border-t border-amber-200/60 animate-slide-up">
          <div className="max-w-3xl mx-auto flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-amber-600">
                  <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
                </svg>
              </div>
              <span className="text-sm text-amber-800 font-medium truncate">Message failed to send</span>
            </div>
            <button
              onClick={handleRetry}
              className="px-4 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-sm font-semibold rounded-xl transition-all duration-200 shadow-md shadow-amber-200/40 hover:shadow-lg flex-shrink-0"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {isCompleted ? (
        <CompletionBanner onNavigate={handleNavigateDashboard} />
      ) : (
        <>
          {currentQuestion?.options && currentQuestion.options.length > 0 && (
            <McqOptions
              options={currentQuestion.options}
              onSelect={handleMcqSelect}
              disabled={loading}
            />
          )}
          {showTextInput && (
            <div className="relative">
              {showTextNudge && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-40 animate-slide-up">
                  <div className="relative bg-teal-600 text-white text-xs font-medium px-4 py-2.5 rounded-xl shadow-lg shadow-teal-200/50 whitespace-nowrap">
                    Feel free to share more details using the text field below
                    <button
                      onClick={() => { setShowTextNudge(false); if (nudgeTimerRef.current) clearTimeout(nudgeTimerRef.current); }}
                      className="ml-2 text-teal-200 hover:text-white"
                    >
                      ✕
                    </button>
                    {/* Arrow pointing down */}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-teal-600" />
                  </div>
                </div>
              )}
              <ChatInput
                onSend={handleTextSend}
                disabled={loading || isCompleted}
                placeholder={inputPlaceholder}
                validationFeedback={inputFeedback}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
