'use client';

import { useEffect, useRef, useState } from 'react';
import { McqOption } from '@/src/types/chat';

interface McqOptionsProps {
  options: McqOption[];
  allowText: boolean;
  disabled: boolean;
  // Legacy path — fires when allowText=false and a chip is clicked.
  onSelect: (option: McqOption) => void;
  // Combined path — fires when allowText=true and the user hits Send.
  // `resolvedOption` is the chip value (or null if they only typed).
  onSend: (content: string, resolvedOption: string | null) => void;
  // Reset internal state when the question changes.
  resetKey?: string;
}

export default function McqOptions({
  options,
  allowText,
  disabled,
  onSelect,
  onSend,
  resetKey,
}: McqOptionsProps) {
  const [text, setText] = useState('');
  const [picked, setPicked] = useState<McqOption | null>(null);
  const [confirmReplace, setConfirmReplace] = useState<McqOption | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Reset local state when the question changes.
  useEffect(() => {
    setText('');
    setPicked(null);
    setConfirmReplace(null);
  }, [resetKey]);

  if (!allowText) {
    return (
      <div className="px-3 py-2.5 sm:px-6 sm:py-3 border-t border-gray-100/80 bg-gradient-to-t from-gray-50/90 to-white/80 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto">
          <div className="flex flex-wrap gap-1.5 sm:grid sm:grid-cols-2 sm:gap-2.5">
            {options.map((option, index) => (
              <ChipButton
                key={option.value}
                option={option}
                index={index}
                selected={false}
                disabled={disabled}
                onClick={() => onSelect(option)}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  const applyOption = (option: McqOption) => {
    setPicked(option);
    setText(option.label);
    setConfirmReplace(null);
    // Focus so the user can immediately keep typing.
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  const handleChipClick = (option: McqOption) => {
    if (disabled) return;
    const trimmed = text.trim();
    const pickedLabel = (picked?.label ?? '').trim();
    // If user typed past the current label, confirm before replacing.
    if (trimmed && trimmed !== pickedLabel) {
      setConfirmReplace(option);
      return;
    }
    applyOption(option);
  };

  const canSend = (picked !== null) || text.trim().length > 0;

  const handleSend = () => {
    if (!canSend || disabled) return;
    const finalText = text.trim() || picked?.label || '';
    onSend(finalText, picked?.value ?? null);
    // Local reset — parent will also swap resetKey when the new question arrives.
    setText('');
    setPicked(null);
    setConfirmReplace(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="px-3 py-2.5 sm:px-6 sm:py-3 border-t border-gray-100/80 bg-gradient-to-t from-gray-50/90 to-white/80 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto space-y-2.5">
        {/* Text box on top */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={2}
            placeholder={picked ? 'Add any extra detail…' : 'Pick an option below, or type your own answer…'}
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

        {/* Options below */}
        <div className="flex flex-wrap gap-1.5 sm:grid sm:grid-cols-2 sm:gap-2.5">
          {options.map((option, index) => (
            <ChipButton
              key={option.value}
              option={option}
              index={index}
              selected={picked?.value === option.value}
              disabled={disabled}
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

        {/* Confirm replace dialog (inline) */}
        {confirmReplace && (
          <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-center justify-between gap-3">
            <span>
              Replace your typed text with <strong>{confirmReplace.label}</strong>?
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => applyOption(confirmReplace)}
                className="px-3 py-1 rounded-lg bg-amber-500 hover:bg-amber-600 text-white font-semibold"
              >
                Replace
              </button>
              <button
                type="button"
                onClick={() => setConfirmReplace(null)}
                className="px-3 py-1 rounded-lg bg-white hover:bg-amber-100 text-amber-800 border border-amber-200"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ChipButton({
  option,
  index,
  selected,
  disabled,
  onClick,
}: {
  option: McqOption;
  index: number;
  selected: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-pressed={selected}
      aria-label={`Select: ${option.label}`}
      className={`group flex-1 min-w-[calc(50%-4px)] sm:min-w-0 min-h-[38px] sm:min-h-[48px] px-3 py-2 sm:px-4 sm:py-3
        border rounded-xl sm:rounded-2xl shadow-sm
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
      <span className="flex items-center gap-2.5">
        <span
          className={`w-6 h-6 sm:w-7 sm:h-7 rounded-lg border flex items-center justify-center text-[0.625rem] sm:text-[0.6875rem] font-bold flex-shrink-0 transition-all duration-200 shadow-sm ${
            selected
              ? 'bg-white/20 text-white border-white/40'
              : 'bg-gradient-to-br from-gray-100 to-gray-50 text-gray-500 border-gray-200/80 group-hover:from-teal-100 group-hover:to-teal-50 group-hover:text-teal-600 group-hover:border-teal-200'
          }`}
        >
          {String.fromCharCode(65 + index)}
        </span>
        <span className="text-xs sm:text-sm font-medium leading-tight">{option.label}</span>
      </span>
    </button>
  );
}
