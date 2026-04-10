"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

type PageState =
  | { kind: "loading" }
  | { kind: "password_setup"; user_email: string; assignment_id?: string }
  | { kind: "auto_login" }
  | { kind: "error"; message: string };

export default function MagicLinkPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const [state, setState] = useState<PageState>({ kind: "loading" });

  // Password setup form
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  // Store response data for later use
  const [responseData, setResponseData] = useState<{
    access_token?: string;
    user?: Record<string, unknown>;
    assignment_id?: string;
  }>({});

  useEffect(() => {
    if (!token) return;

    const verifyToken = async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/magic-login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });

        if (!response.ok) {
          setState({
            kind: "error",
            message: "This link has expired or is invalid.",
          });
          return;
        }

        const data = await response.json();
        setResponseData(data);

        if (data.needs_password_setup) {
          setState({
            kind: "password_setup",
            user_email: data.user_email || "",
            assignment_id: data.assignment_id,
          });
        } else {
          // Auto-login
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("user", JSON.stringify(data.user));
          setState({ kind: "auto_login" });

          setTimeout(() => {
            if (data.assignment_id) {
              router.push(`/chat/${data.assignment_id}`);
            } else {
              router.push("/dashboard");
            }
          }, 1200);
        }
      } catch {
        setState({
          kind: "error",
          message: "This link has expired or is invalid.",
        });
      }
    };

    verifyToken();
  }, [token, router]);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");

    if (password.length < 8) {
      setFormError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setFormError("Passwords do not match.");
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(`${API_BASE}/auth/setup-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password, confirm_password: confirmPassword }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => null);
        setFormError(err?.detail || "Failed to set password. Please try again.");
        setSubmitting(false);
        return;
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      const assignmentId = data.assignment_id || responseData.assignment_id;
      if (assignmentId) {
        router.push(`/chat/${assignmentId}`);
      } else {
        router.push("/dashboard");
      }
    } catch {
      setFormError("An error occurred. Please try again.");
      setSubmitting(false);
    }
  };

  // --- Eye icon SVGs ---
  const EyeOpen = (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );

  const EyeClosed = (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
    </svg>
  );

  // --- Render states ---

  const renderLoading = () => (
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-[#dedede] border-t-[#00acb6] rounded-full animate-spin mx-auto mb-6" />
      <h2 className="font-serif text-[1.5rem] text-[#333] mb-2">
        Verifying your link...
      </h2>
      <p className="text-[#737373] text-[0.9375rem]">Please wait while we verify your invitation.</p>
    </div>
  );

  const renderAutoLogin = () => (
    <div className="text-center">
      <div className="w-16 h-16 bg-[#e6f7f8] border border-[#00acb6] rounded-full flex items-center justify-center mx-auto mb-6">
        <svg className="w-8 h-8 text-[#00acb6]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 className="font-serif text-[1.5rem] text-[#333] mb-2">
        Logging you in...
      </h2>
      <p className="text-[#737373] text-[0.9375rem]">You will be redirected momentarily.</p>
    </div>
  );

  const renderError = (message: string) => (
    <div className="text-center">
      <div className="bg-white border border-[#e61844] rounded p-6 mb-8">
        <div className="w-12 h-12 bg-[#fdecec] border border-[#e61844] rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-[#e61844]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 className="font-serif text-[1.375rem] text-[#333] mb-2">
          {message}
        </h2>
        <p className="text-[#737373] text-[0.9375rem]">
          Please contact your psychologist for a new invitation link.
        </p>
      </div>
      <button
        onClick={() => router.push("/login")}
        className="w-full py-3 bg-[#e61844] hover:bg-[#cf0627] text-white font-semibold rounded transition-colors text-[1rem] border border-[#e61844] hover:border-[#cf0627]"
      >
        Go to Login
      </button>
    </div>
  );

  const renderPasswordSetup = (userEmail: string) => (
    <div>
      <div className="mb-8">
        <h2 className="font-serif text-[1.875rem] text-[#333] mb-3">
          Welcome to <span className="text-[#00a1aa]">The Ed Psych Practice</span>
        </h2>
        <p className="text-[#737373] text-[1rem] leading-[1.8]">
          Set up your password to access your child&apos;s assessment.
        </p>
      </div>

      <div className="bg-[#e6f7f8] border border-[#00acb6] rounded px-4 py-3 mb-6 flex items-center gap-3">
        <svg className="w-5 h-5 text-[#0c888e] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
        </svg>
        <span className="text-[0.9375rem] text-[#0c888e] font-semibold truncate">{userEmail}</span>
      </div>

      <form onSubmit={handlePasswordSubmit} className="space-y-5">
        {formError && (
          <div className="bg-[#fdecec] border border-[#e61844] rounded px-4 py-3 text-[0.875rem] text-[#e61844] font-semibold">
            {formError}
          </div>
        )}

        {/* Password Field */}
        <div className="relative">
          <label htmlFor="password" className="block text-[0.8125rem] font-semibold text-[#333] mb-1.5">
            Password (min 8 characters)
          </label>
          <input
            type={showPassword ? "text" : "password"}
            id="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3 bg-white border border-[#ccc] rounded focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] outline-none transition-all text-[1rem] text-[#333]"
            required
            minLength={8}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-[38px] text-[#737373] hover:text-[#00acb6] transition-colors"
          >
            {showPassword ? EyeClosed : EyeOpen}
          </button>
        </div>

        {/* Confirm Password Field */}
        <div className="relative">
          <label htmlFor="confirmPassword" className="block text-[0.8125rem] font-semibold text-[#333] mb-1.5">
            Confirm Password
          </label>
          <input
            type={showConfirmPassword ? "text" : "password"}
            id="confirmPassword"
            name="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full px-4 py-3 bg-white border border-[#ccc] rounded focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] outline-none transition-all text-[1rem] text-[#333]"
            required
            minLength={8}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-3 top-[38px] text-[#737373] hover:text-[#00acb6] transition-colors"
          >
            {showConfirmPassword ? EyeClosed : EyeOpen}
          </button>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 bg-[#e61844] hover:bg-[#cf0627] text-white font-semibold rounded transition-colors disabled:opacity-50 text-[1rem] border border-[#e61844] hover:border-[#cf0627]"
        >
          {submitting ? "Setting up..." : "Create Password & Continue"}
        </button>
      </form>
    </div>
  );

  // --- Main content selector ---
  const renderContent = () => {
    switch (state.kind) {
      case "loading":
        return renderLoading();
      case "auto_login":
        return renderAutoLogin();
      case "error":
        return renderError(state.message);
      case "password_setup":
        return renderPasswordSetup(state.user_email);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Top teal nav — matches theedpsych.com */}
      <div className="ed-nav w-full py-3 px-6">
        <span className="text-white font-serif text-xl tracking-wide">The Ed Psych Practice</span>
      </div>

      <div className="flex-1 flex items-stretch">
        {/* Left Section: Welcome hero with cherry-blossom corner accents */}
        <section className="hidden lg:flex w-6/12 relative ed-hero items-center justify-center p-16 border-r border-[#dedede] overflow-hidden">
          <img
            src="/images/cherry-tree.png"
            alt=""
            aria-hidden="true"
            className="absolute top-0 left-0 w-[320px] opacity-40 pointer-events-none select-none"
          />
          <img
            src="/images/cherry-tree.png"
            alt=""
            aria-hidden="true"
            className="absolute bottom-0 right-0 w-[280px] opacity-30 pointer-events-none select-none transform scale-x-[-1]"
          />
          <div className="relative z-10 max-w-xl w-full text-center">
            <div className="mb-8">
              <h1 className="brand-wordmark mb-2">The Ed Psych Practice</h1>
              <p className="brand-tagline">An Independent Practice in Central London</p>
            </div>

            <div className="w-20 h-[2px] bg-[#00acb6] mx-auto mb-8" />

            <h2 className="font-serif text-[1.875rem] leading-[1.3] text-[#333] mb-6">
              Your <span className="text-[#00a1aa]">Assessment Portal</span>
            </h2>
            <p className="text-[1.125rem] leading-[1.8] text-[#737373] max-w-md mx-auto mb-10">
              Your psychologist has invited you to securely access your child&apos;s
              assessment. Set up your account to get started.
            </p>

            <div className="ed-card max-w-md mx-auto">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-[#e6f7f8] border border-[#00acb6] rounded-full flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-[#00acb6]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <div className="text-left">
                  <h3 className="font-serif text-[1.125rem] text-[#333] mb-1">Secure Access</h3>
                  <p className="text-[0.875rem] text-[#737373]">Your data is encrypted and protected</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Right Section: Content */}
        <main className="w-full lg:w-6/12 bg-white flex flex-col items-center justify-center p-8 sm:p-16 relative">
          {/* Mobile branding */}
          <div className="lg:hidden absolute top-6 left-6">
            <h1 className="font-serif text-2xl text-[#0c888e]">The Ed Psych Practice</h1>
          </div>

          <div className="max-w-md w-full mt-16 lg:mt-0">
            {renderContent()}

            <footer className="mt-12 text-center">
              <div className="flex justify-center gap-6 text-[0.6875rem] font-semibold uppercase tracking-[0.15em] text-[#737373]">
                <a href="#" className="hover:text-[#e61844] transition-colors">Documentation</a>
                <a href="#" className="hover:text-[#e61844] transition-colors">Support</a>
                <a href="#" className="hover:text-[#e61844] transition-colors">Privacy</a>
              </div>
              <div className="mt-6 text-[0.75rem] text-[#737373]">
                &copy; 2026 The Ed Psych Practice. All clinical data encrypted.
              </div>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}
