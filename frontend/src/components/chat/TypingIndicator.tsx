'use client';

export default function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 sm:gap-2.5 justify-start msg-bot-enter" role="status" aria-label="Preparing response">
      {/* Bot Avatar */}
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-500 via-teal-600 to-teal-600 flex items-center justify-center flex-shrink-0 mb-0.5 shadow-md shadow-teal-200/40 avatar-glow">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
          <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7Z" />
          <path d="M10 21h4" />
          <path d="M12 6v4" />
          <path d="M10 10h4" />
        </svg>
      </div>

      <div className="bg-white rounded-2xl rounded-bl-md px-5 py-3.5 shadow-sm border border-gray-100">
        <div className="flex items-center gap-1.5">
          <span className="typing-dot inline-block w-2 h-2 rounded-full bg-teal-400" />
          <span className="typing-dot inline-block w-2 h-2 rounded-full bg-teal-400" />
          <span className="typing-dot inline-block w-2 h-2 rounded-full bg-teal-400" />
        </div>
      </div>
    </div>
  );
}
