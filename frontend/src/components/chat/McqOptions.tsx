'use client';

import { McqOption } from '@/src/types/chat';

interface McqOptionsProps {
  options: McqOption[];
  onSelect: (option: McqOption) => void;
  disabled: boolean;
}

export default function McqOptions({ options, onSelect, disabled }: McqOptionsProps) {
  return (
    <div className="px-3 py-2.5 sm:px-6 sm:py-3 border-t border-gray-100/80 bg-gradient-to-t from-gray-50/90 to-white/80 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto">
        <div className="flex flex-wrap gap-1.5 sm:grid sm:grid-cols-2 sm:gap-2.5">
          {options.map((option, index) => (
            <button
              key={option.value}
              onClick={() => onSelect(option)}
              disabled={disabled}
              aria-label={`Select: ${option.label}`}
              className={`group flex-1 min-w-[calc(50%-4px)] sm:min-w-0 min-h-[38px] sm:min-h-[48px] px-3 py-2 sm:px-4 sm:py-3
                bg-white border border-gray-200/80
                text-gray-700 rounded-xl sm:rounded-2xl
                hover:bg-gradient-to-br hover:from-teal-50 hover:to-teal-50/50
                hover:border-teal-300 hover:text-teal-900
                hover:shadow-lg hover:shadow-teal-100/40
                hover:-translate-y-0.5
                active:translate-y-0 active:shadow-md active:bg-teal-50
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus-visible:ring-offset-1
                transition-all duration-200 ease-out
                disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none
                text-left mcq-option-enter shadow-sm`}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <span className="flex items-center gap-2.5">
                <span className="w-6 h-6 sm:w-7 sm:h-7 rounded-lg bg-gradient-to-br from-gray-100 to-gray-50 text-gray-500
                  group-hover:from-teal-100 group-hover:to-teal-50 group-hover:text-teal-600
                  border border-gray-200/80 group-hover:border-teal-200
                  flex items-center justify-center text-[0.625rem] sm:text-[0.6875rem] font-bold flex-shrink-0
                  transition-all duration-200 shadow-sm">
                  {String.fromCharCode(65 + index)}
                </span>
                <span className="text-xs sm:text-sm font-medium leading-tight">
                  {option.label}
                </span>
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
