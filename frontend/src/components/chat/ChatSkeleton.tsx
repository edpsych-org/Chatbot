'use client';

export default function ChatSkeleton() {
  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-slate-50 via-gray-50 to-gray-100/80">
      {/* Header skeleton */}
      <div className="bg-white/95 backdrop-blur-md border-b border-gray-200/60 px-3 py-2.5 sm:px-6 sm:py-3">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl skeleton-shimmer" />
          <div className="flex-1 space-y-1.5">
            <div className="h-4 w-36 rounded-lg skeleton-shimmer" />
            <div className="h-3 w-24 rounded-lg skeleton-shimmer hidden sm:block" />
          </div>
          <div className="h-8 w-20 rounded-lg skeleton-shimmer" />
        </div>
      </div>

      {/* Progress bar skeleton */}
      <div className="bg-white/80 border-b border-gray-100/60 px-3 py-2.5 sm:px-6 sm:py-3">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between mb-2">
            <div className="h-3 w-28 rounded skeleton-shimmer" />
            <div className="h-3 w-8 rounded skeleton-shimmer" />
          </div>
          <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full w-0 rounded-full" />
          </div>
        </div>
      </div>

      {/* Message bubbles skeleton */}
      <div className="flex-1 overflow-hidden px-3 py-5 sm:px-6 sm:py-8">
        <div className="max-w-3xl mx-auto space-y-5">
          {/* Bot message skeleton 1 */}
          <div className="flex items-end gap-2.5 justify-start animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="w-8 h-8 rounded-xl skeleton-shimmer flex-shrink-0" />
            <div className="max-w-[72%] rounded-2xl rounded-bl-md px-4 py-3 bg-white border border-gray-100 shadow-sm">
              <div className="space-y-2">
                <div className="h-3.5 w-56 rounded skeleton-shimmer" />
                <div className="h-3.5 w-44 rounded skeleton-shimmer" />
              </div>
              <div className="h-2.5 w-10 rounded skeleton-shimmer mt-2.5" />
            </div>
          </div>

          {/* User message skeleton */}
          <div className="flex items-end gap-2.5 justify-end animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <div className="max-w-[72%] rounded-2xl rounded-br-md px-4 py-3 bg-teal-100/60 shadow-sm">
              <div className="h-3.5 w-32 rounded skeleton-shimmer" />
              <div className="h-2.5 w-10 rounded skeleton-shimmer mt-2.5" />
            </div>
            <div className="w-8 h-8 rounded-xl skeleton-shimmer flex-shrink-0" />
          </div>

          {/* Bot message skeleton 2 */}
          <div className="flex items-end gap-2.5 justify-start animate-fade-in" style={{ animationDelay: '0.5s' }}>
            <div className="w-8 h-8 rounded-xl skeleton-shimmer flex-shrink-0" />
            <div className="max-w-[72%] rounded-2xl rounded-bl-md px-4 py-3 bg-white border border-gray-100 shadow-sm">
              <div className="space-y-2">
                <div className="h-3.5 w-64 rounded skeleton-shimmer" />
                <div className="h-3.5 w-48 rounded skeleton-shimmer" />
                <div className="h-3.5 w-36 rounded skeleton-shimmer" />
              </div>
              <div className="h-2.5 w-10 rounded skeleton-shimmer mt-2.5" />
            </div>
          </div>
        </div>
      </div>

      {/* Input skeleton */}
      <div className="bg-white/95 backdrop-blur-md border-t border-gray-200/60 px-3 py-2.5 sm:px-6 sm:py-3">
        <div className="max-w-3xl mx-auto flex gap-2.5 items-center">
          <div className="flex-1 min-h-[46px] rounded-2xl skeleton-shimmer" />
          <div className="min-h-[46px] min-w-[46px] rounded-2xl skeleton-shimmer" />
        </div>
      </div>
    </div>
  );
}
