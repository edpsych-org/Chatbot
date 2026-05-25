"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

export default function ResetPasswordPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const token = params?.token ?? "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token,
          password,
          confirm_password: confirmPassword,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        setError(data?.detail || "Couldn't reset your password. The link may be invalid or expired.");
        return;
      }

      setSuccess(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (err) {
      console.error("Reset password error:", err);
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <div className="ed-nav w-full py-3 px-6 flex items-center justify-between border-b border-[#00acb6]">
        <div className="flex items-center gap-3">
          <span className="text-white font-serif text-xl tracking-wide">The Ed Psych Practice</span>
        </div>
      </div>

      <main className="flex-1 flex flex-col items-center justify-center p-8 sm:p-16">
        <div className="max-w-md w-full">
          <div className="mb-8">
            <h2 className="font-serif text-[1.875rem] text-[#333] mb-3">Choose a new password</h2>
            <p className="text-[1rem] text-[#737373]">
              Enter a new password for your account. Use at least 8 characters.
            </p>
          </div>

          {success ? (
            <div className="space-y-5">
              <div className="p-4 bg-[#e6f7f8] border border-[#00acb6]/30 rounded">
                <p className="text-[0.9375rem] text-[#0c888e]">
                  ✅ Password reset successfully. Redirecting you to sign in…
                </p>
              </div>
              <Link href="/login" className="inline-block text-[0.875rem] font-semibold text-[#00acb6] hover:text-[#0c888e]">
                Go to sign in now →
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="relative">
                <label htmlFor="password" className="block text-[0.8125rem] font-semibold text-[#333] mb-1.5">
                  New password
                </label>
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-white border border-[#ccc] rounded focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] outline-none transition-all text-[1rem] text-[#333]"
                  minLength={8}
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-[38px] text-[#737373] hover:text-[#00acb6] transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>

              <div>
                <label htmlFor="confirm" className="block text-[0.8125rem] font-semibold text-[#333] mb-1.5">
                  Confirm password
                </label>
                <input
                  type={showPassword ? "text" : "password"}
                  id="confirm"
                  name="confirm"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-white border border-[#ccc] rounded focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] outline-none transition-all text-[1rem] text-[#333]"
                  minLength={8}
                  required
                  autoComplete="new-password"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-[0.875rem] text-red-700">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !password || !confirmPassword}
                className="w-full py-3 bg-[#e61844] hover:bg-[#cf0627] text-white font-semibold rounded transition-colors duration-150 disabled:opacity-50 text-[1rem] border border-[#e61844] hover:border-[#cf0627]"
              >
                {loading ? "Resetting…" : "Reset password"}
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
