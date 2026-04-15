"use client";

import { useEffect } from "react";
import { reportClientError } from "@/src/lib/logger";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    reportClientError(error, { digest: error.digest, boundary: "route" });
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl max-w-md w-full text-center">
        <div className="w-14 h-14 rounded-full bg-red-50 text-red-500 mx-auto mb-4 flex items-center justify-center">
          <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h2 className="text-lg font-bold text-on-background mb-1">Something went wrong</h2>
        <p className="text-sm text-slate-500 mb-5">
          The issue has been logged. You can retry or return to the previous page.
        </p>
        <button
          onClick={reset}
          className="px-5 py-2.5 bg-primary text-white font-bold rounded-xl hover:bg-teal-600 transition-all"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
