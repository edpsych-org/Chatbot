'use client';

import { useEffect, useRef, useState } from 'react';
import { McqOption } from '@/src/types/chat';

interface McqOptionsProps {
  options: McqOption[];
  allowText: boolean;
  disabled: boolean;
  onSelect: (option: McqOption) => void;
  onSend: (content: string, resolvedOption: string | null) => void;
  resetKey?: string;
  // Optional "feel free to type" nudge rendered above the text box.
  showNudge?: boolean;
  nudgeColor?: number;
  onDismissNudge?: () => void;
}

const NUDGE_PALETTE = [
  { bg: '#a855f7', arrow: 'border-t-[#a855f7]' }, // purple
  { bg: '#ec4899', arrow: 'border-t-[#ec4899]' }, // pink
  { bg: '#3b82f6', arrow: 'border-t-[#3b82f6]' }, // blue
];

export default function McqOptions({
  options,
  allowText,
  disabled,
  onSelect,
  onSend,
  resetKey,
  showNudge = false,
  nudgeColor = 0,
  onDismissNudge,
}: McqOptionsProps) {
  const [text, setText] = useState('');
  const [picked, setPicked] = useState<McqOption | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Reset local state when the question changes.
  useEffect(() => {
    setText('');
    setPicked(null);
  }, [resetKey]);

  // Combined layout is used for every MCQ question, regardless of the
  // node's `allow_text` flag. Free-text elaboration is always available
  // so parents/schools can add detail before or after picking an option.
  // (The `allowText` / `onSelect` props are kept for backwards compat.)
  void allowText;
  void onSelect;

  const handleChipClick = (option: McqOption) => {
    if (disabled) return;
    // Selecting an option copies its label into the textarea so the user can
    // edit or append detail from there. Picking a different option replaces
    // the textarea with the new label.
    setPicked(option);
    setText(option.label);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (el) {
        el.focus();
        // Place cursor at end so the user can keep typing after the label.
        const len = option.label.length;
        try { el.setSelectionRange(len, len); } catch { /* ignore */ }
      }
    });
  };

  const canSend = (picked !== null) || text.trim().length > 0;

  const handleSend = () => {
    if (!canSend || disabled) return;
    const finalText = text.trim() || picked?.label || '';
    onSend(finalText, picked?.value ?? null);
    // Local reset — parent will also swap resetKey when the new question arrives.
    setText('');
    setPicked(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const nudge = NUDGE_PALETTE[nudgeColor % NUDGE_PALETTE.length];

  return (
    <div className="px-3 py-2.5 sm:px-6 sm:py-3 border-t border-gray-100/80 bg-gradient-to-t from-gray-50/90 to-white/80 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto space-y-2">
        {/* Text box on top */}
        <div className="relative">
          {showNudge && (
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-40 animate-slide-up w-full px-2 sm:px-0 sm:w-auto sm:max-w-[min(90vw,420px)] pointer-events-none">
              <div
                className="relative text-white text-[0.6875rem] sm:text-xs font-medium px-3 py-2 sm:px-4 sm:py-2.5 rounded-xl shadow-lg leading-snug flex items-start gap-2 pointer-events-auto"
                style={{ backgroundColor: nudge.bg }}
              >
                <span className="flex-1 break-words">
                  <span className="hidden sm:inline">Feel free to share more details in the text box</span>
                  <span className="sm:hidden">Add details in the text box</span>
                </span>
                <button
                  onClick={() => onDismissNudge?.()}
                  aria-label="Dismiss"
                  className="text-white/70 hover:text-white flex-shrink-0 leading-none"
                >
                  ✕
                </button>
                <div className={`absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] ${nudge.arrow}`} />
              </div>
            </div>
          )}
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={2}
            placeholder={picked ? 'Edit or add more detail…' : 'Pick an option below, or type your own answer…'}
            className="w-full px-3 py-2.5 text-sm bg-white border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-teal-400/30 focus:border-teal-400 resize-none placeholder:text-gray-400 disabled:opacity-50"
          />
          {picked && (
            <div className="mt-1.5 text-[0.6875rem] text-teal-700 flex items-center gap-1.5">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-teal-50 border border-teal-100">
                Option selected: <strong className="font-semibold">{picked.label}</strong>
              </span>
              <button
                type="button"
                onClick={() => { setPicked(null); setText(''); }}
                className="underline text-gray-500 hover:text-gray-700"
                disabled={disabled}
              >
                clear
              </button>
            </div>
          )}
        </div>

        {/* Options below — compact layout in combined panel */}
        <div className="flex flex-wrap gap-1.5 sm:grid sm:grid-cols-2 sm:gap-1.5">
          {options.map((option, index) => (
            <ChipButton
              key={option.value}
              option={option}
              index={index}
              selected={picked?.value === option.value}
              disabled={disabled}
              compact
              onClick={() => handleChipClick(option)}
            />
          ))}
        </div>

        {/* Send row */}
        <div className="flex items-center justify-end">
          <button
            type="button"
            onClick={handleSend}
            disabled={!canSend || disabled}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-600 text-white text-sm font-semibold shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Send
            <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M3.105 3.105a1.5 1.5 0 0 1 1.59-.34l12 4.5a1.5 1.5 0 0 1 0 2.78l-12 4.5a1.5 1.5 0 0 1-2.011-1.84l1.214-4.05H9a.75.75 0 0 0 0-1.5H3.898L2.684 4.945a1.5 1.5 0 0 1 .42-1.84Z" />
            </svg>
          </button>
        </div>

      </div>
    </div>
  );
}

function ChipButton({
  option,
  index,
  selected,
  disabled,
  compact = false,
  onClick,
}: {
  option: McqOption;
  index: number;
  selected: boolean;
  disabled: boolean;
  compact?: boolean;
  onClick: () => void;
}) {
  const sizeClasses = compact
    ? 'min-h-[30px] sm:min-h-[34px] px-2.5 py-1.5 rounded-lg'
    : 'min-h-[38px] sm:min-h-[48px] px-3 py-2 sm:px-4 sm:py-3 rounded-xl sm:rounded-2xl';
  const badgeClasses = compact
    ? 'w-4 h-4 sm:w-5 sm:h-5 rounded-md text-[0.5625rem] sm:text-[0.625rem]'
    : 'w-6 h-6 sm:w-7 sm:h-7 rounded-lg text-[0.625rem] sm:text-[0.6875rem]';
  const labelClasses = compact
    ? 'text-[0.6875rem] sm:text-xs font-medium leading-tight'
    : 'text-xs sm:text-sm font-medium leading-tight';
  const gap = compact ? 'gap-1.5' : 'gap-2.5';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-pressed={selected}
      aria-label={`Select: ${option.label}`}
      className={`group flex-1 min-w-[calc(50%-4px)] sm:min-w-0 ${sizeClasses}
        border shadow-sm
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus-visible:ring-offset-1
        transition-all duration-200 ease-out
        disabled:opacity-40 disabled:cursor-not-allowed
        text-left mcq-option-enter ${
          selected
            ? 'bg-gradient-to-br from-teal-500 to-teal-600 text-white border-teal-500 shadow-md shadow-teal-200/50'
            : 'bg-white border-gray-200/80 text-gray-700 hover:bg-gradient-to-br hover:from-teal-50 hover:to-teal-50/50 hover:border-teal-300 hover:text-teal-900 hover:shadow-lg hover:shadow-teal-100/40 hover:-translate-y-0.5 active:translate-y-0 active:shadow-md active:bg-teal-50'
        }`}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <span className={`flex items-center ${gap}`}>
        <span
          className={`${badgeClasses} border flex items-center justify-center font-bold flex-shrink-0 transition-all duration-200 shadow-sm ${
            selected
              ? 'bg-white/20 text-white border-white/40'
              : 'bg-gradient-to-br from-gray-100 to-gray-50 text-gray-500 border-gray-200/80 group-hover:from-teal-100 group-hover:to-teal-50 group-hover:text-teal-600 group-hover:border-teal-200'
          }`}
        >
          {String.fromCharCode(65 + index)}
        </span>
        <span className={labelClasses}>{option.label}</span>
      </span>
    </button>
  );
}
