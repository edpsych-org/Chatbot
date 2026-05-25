"use client";

import { useState } from "react";
import Link from "next/link";
import { API_BASE } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(data?.detail || "Couldn't process that request. Please try again.");
        return;
      }

      setSubmitted(true);
    } catch (err) {
      console.error("Forgot password error:", err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Top teal navigation bar — matches login */}
      <div className="ed-nav w-full py-3 px-6 flex items-center justify-between border-b border-[#00acb6]">
        <div className="flex items-center gap-3">
          <span className="text-white font-serif text-xl tracking-wide">The Ed Psych Practice</span>
        </div>
      </div>

      <main className="flex-1 flex flex-col items-center justify-center p-8 sm:p-16">
        <div className="max-w-md w-full">
          <div className="mb-8">
            <h2 className="font-serif text-[1.875rem] text-[#333] mb-3">Forgot your password?</h2>
            <p className="text-[1rem] text-[#737373]">
              Enter the email address associated with your account and we&apos;ll send you a link to reset your password.
            </p>
          </div>

          {submitted ? (
            <div className="space-y-5">
              <div className="p-4 bg-[#e6f7f8] border border-[#00acb6]/30 rounded">
                <p className="text-[0.9375rem] text-[#0c888e]">
                  If an account exists for <strong>{email}</strong>, a password-reset link has been sent.
                  The link expires in 1 hour.
                </p>
              </div>
              <p className="text-[0.875rem] text-[#737373]">
                Didn&apos;t get the email? Check your spam folder, or{" "}
                <button
                  type="button"
                  onClick={() => { setSubmitted(false); setEmail(""); }}
                  className="font-semibold text-[#e61844] hover:text-[#cf0627] underline"
                >
                  try a different email
                </button>
                .
              </p>
              <Link href="/login" className="inline-block text-[0.875rem] font-semibold text-[#00acb6] hover:text-[#0c888e]">
                ← Back to sign in
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-[0.8125rem] font-semibold text-[#333] mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-white border border-[#ccc] rounded focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] outline-none transition-all text-[1rem] text-[#333]"
                  placeholder="you@example.com"
                  required
                  autoComplete="email"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-[0.875rem] text-red-700">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !email.trim()}
                className="w-full py-3 bg-[#e61844] hover:bg-[#cf0627] text-white font-semibold rounded transition-colors duration-150 disabled:opacity-50 text-[1rem] border border-[#e61844] hover:border-[#cf0627]"
              >
                {loading ? "Sending..." : "Send reset link"}
              </button>

              <div className="text-center">
                <Link href="/login" className="text-[0.875rem] font-semibold text-[#00acb6] hover:text-[#0c888e]">
                  ← Back to sign in
                </Link>
              </div>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
