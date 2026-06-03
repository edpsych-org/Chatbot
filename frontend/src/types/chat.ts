export type AssessmentCategory =
  | 'attention'
  | 'social'
  | 'emotional'
  | 'academic'
  | 'behavioral';

export interface McqOption {
  value: string;
  label: string;
  metadata?: {
    severity?: string;
    next?: string;
  };
}

export interface QuestionMetadata {
  question?: string;
  question_id?: string;
  node_id?: string;
  options?: McqOption[];
  allow_text?: boolean;
  text_prompt?: string;
  validation?: boolean;
  category?: string;
  multi_select?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'bot' | 'system';
  message_type: 'text' | 'mcq_choice' | 'adaptive_question' | 'system_message' | 'mcq' | 'text_only' | 'completion';
  content: string;
  metadata?: QuestionMetadata;
  timestamp: string;
  isValidationFeedback?: boolean;
  // Edit support (last user message only)
  resolvedOption?: string | null;
  // Question context snapshotted so we can render chips in edit mode.
  questionId?: string | null;
  questionOptions?: McqOption[] | null;
  editedAt?: string | null;
  skipped?: boolean;
}

export interface EditMessagePayload {
  content: string;
  resolved_option: string | null;
}

export interface BotResponse {
  bot_message: {
    message_type: string;
    content: string;
    metadata?: QuestionMetadata;
  };
  user_message_id?: string | null;
  progress_percentage: number;
  status: 'in_progress' | 'completed';
  is_complete: boolean;
  current_category?: string;
  input_feedback?: string;
}

export interface SessionStartResponse {
  session_id: string;
  bot_message: {
    message_type: string;
    content: string;
    metadata?: QuestionMetadata;
  };
  metadata?: Record<string, unknown>;
}

export interface ChatSession {
  sessionId: string;
  assignmentId: string;
  status: string;
  progress: number;
  messages: ChatMessage[];
}
