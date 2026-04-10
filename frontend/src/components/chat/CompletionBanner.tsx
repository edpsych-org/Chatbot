'use client';

import { useEffect, useState } from 'react';

interface CompletionBannerProps {
  onNavigate: () => void;
}

const CONFETTI_COLORS = [
  'bg-teal-400', 'bg-teal-400', 'bg-emerald-400',
  'bg-pink-400', 'bg-amber-400', 'bg-teal-400',
];

export default function CompletionBanner({ onNavigate }: CompletionBannerProps) {
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowConfetti(true), 300);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="px-4 py-8 sm:px-6 sm:py-12 animate-celebrate-in relative overflow-hidden">
      {/* Confetti particles */}
      {showConfetti && (
        <div className="absolute inset-0 pointer-events-none">
          {Array.from({ length: 12 }).map((_, i) => (
            <div
              key={i}
              className={`confetti-particle ${CONFETTI_COLORS[i % CONFETTI_COLORS.length]}`}
              style={{
                left: `${10 + (i * 7.5)}%`,
                top: `${40 + Math.random() * 30}%`,
                animationDelay: `${i * 0.1}s`,
                animationDuration: `${1.2 + Math.random() * 0.8}s`,
              }}
            />
          ))}
        </div>
      )}

      <div className="max-w-sm mx-auto text-center relative">
        {/* Success icon */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="w-20 h-20 bg-gradient-to-br from-emerald-400 via-emerald-500 to-teal-600 rounded-2xl rotate-3 flex items-center justify-center shadow-xl shadow-emerald-200/50">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="white"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="w-10 h-10"
                aria-hidden="true"
              >
                <polyline points="20 6 9 17 4 12" className="animate-check-draw" />
              </svg>
            </div>
            {/* Decorative rings */}
            <div className="absolute -inset-3 rounded-2xl rotate-3 border-2 border-emerald-200/50 animate-ring-pulse" />
            <div className="absolute -inset-5 rounded-2xl rotate-3 border border-emerald-100/30 animate-ring-pulse" style={{ animationDelay: '0.5s' }} />
          </div>
        </div>

        {/* Text */}
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2.5 tracking-tight">
          Assessment Complete!
        </h2>
        <div className="mb-8" />

        {/* CTA Button */}
        <button
          onClick={onNavigate}
          aria-label="Return to Dashboard"
          className="inline-flex items-center gap-2.5 min-h-[52px]
            bg-gradient-to-r from-teal-500 via-teal-600 to-teal-600
            hover:from-teal-600 hover:via-teal-700 hover:to-teal-700
            text-white px-8 py-3.5 rounded-2xl font-semibold text-sm sm:text-base
            shadow-xl shadow-teal-200/50 hover:shadow-2xl hover:shadow-teal-200/60
            transition-all duration-300 hover:-translate-y-1
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 focus-visible:ring-offset-2
            active:translate-y-0 active:shadow-lg"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
            <path fillRule="evenodd" d="M9.293 2.293a1 1 0 0 1 1.414 0l7 7A1 1 0 0 1 17 10.414l-7-7-7 7A1 1 0 0 1 1.586 9.293l7-7ZM2 17.5A1.5 1.5 0 0 1 3.5 16h13a1.5 1.5 0 0 1 0 3h-13A1.5 1.5 0 0 1 2 17.5Z" clipRule="evenodd" />
          </svg>
          Return to Dashboard
        </button>

      </div>
    </div>
  );
}
