"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    remember: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user", JSON.stringify(data.user));

        // Redirect based on role
        switch (data.user.role.toUpperCase()) {
          case "PSYCHOLOGIST":
            router.push("/psychologist/dashboard");
            break;
          case "SCHOOL":
            router.push("/school/dashboard");
            break;
          case "ADMIN":
            router.push("/admin/dashboard");
            break;
          case "PARENT":
          default:
            router.push("/dashboard");
            break;
        }
      } else {
        alert("Login failed. Please check your credentials.");
      }
    } catch (error) {
      console.error("Login error:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Top teal navigation bar — matches theedpsych.com */}
      <div className="ed-nav w-full py-3 px-6 flex items-center justify-between border-b border-[#00acb6]">
        <div className="flex items-center gap-3">
          <span className="text-white font-serif text-xl tracking-wide">The Ed Psych Practice</span>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-white text-[0.8125rem] uppercase tracking-wider">
          <a href="#" className="hover:opacity-80 text-white">Home</a>
          <a href="#" className="hover:opacity-80 text-white">About</a>
          <a href="#" className="hover:opacity-80 text-white">Services</a>
          <a href="#" className="hover:opacity-80 text-white">Contact</a>
        </nav>
      </div>

      <div className="flex-1 flex items-stretch">
        {/* Left Section: Branding hero with cherry-blossom corner accent */}
        <section className="hidden lg:flex w-6/12 relative ed-hero items-center justify-center p-16 border-r border-[#dedede] overflow-hidden">
          {/* Decorative cherry-blossom (top-left corner, behind content) */}
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
              Assessment <span className="text-[#00a1aa]">Intelligence</span>
            </h2>
            <p className="text-[1.125rem] leading-[1.8] text-[#737373] max-w-md mx-auto mb-10">
              Transforming assessment data into precise, actionable insights.
              Built for practitioners who value clarity and depth.
            </p>

            <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
              <div className="ed-card text-left">
                <div className="text-[0.6875rem] font-bold uppercase tracking-wider text-[#00acb6] mb-1">Insight</div>
                <div className="text-[0.9375rem] text-[#333] font-semibold">Neural synthesis</div>
              </div>
              <div className="ed-card text-left">
                <div className="text-[0.6875rem] font-bold uppercase tracking-wider text-[#00acb6] mb-1">Reliability</div>
                <div className="text-[0.9375rem] text-[#333] font-semibold">98.4% confidence</div>
              </div>
            </div>
          </div>
        </section>

        {/* Right Section: Login Form */}
        <main className="w-full lg:w-6/12 bg-white flex flex-col items-center justify-center p-8 sm:p-16 relative">
          {/* Mobile branding */}
          <div className="lg:hidden absolute top-6 left-6">
            <h1 className="font-serif text-2xl text-[#0c888e]">The Ed Psych Practice</h1>
          </div>

          <div className="max-w-md w-full mt-16 lg:mt-0">
            <div className="mb-8 lg:mb-10">
              <h2 className="font-serif text-[1.875rem] text-[#333] mb-3">Welcome Back</h2>
              <p className="text-[1rem] text-[#737373]">
                Access your dashboard and student assessments.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email Field */}
              <div>
                <label htmlFor="email" className="block text-[0.8125rem] font-semibold text-[#333] mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-3 bg-white border border-[#ccc] rounded focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] outline-none transition-all text-[1rem] text-[#333]"
                  required
                />
              </div>

              {/* Password Field */}
              <div className="relative">
                <label htmlFor="password" className="block text-[0.8125rem] font-semibold text-[#333] mb-1.5">
                  Password
                </label>
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-3 bg-white border border-[#ccc] rounded focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] outline-none transition-all text-[1rem] text-[#333]"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-[38px] text-[#737373] hover:text-[#00acb6] transition-colors"
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

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.remember}
                    onChange={(e) => setFormData({ ...formData, remember: e.target.checked })}
                    className="w-4 h-4 rounded border-[#ccc] text-[#00acb6] focus:ring-[#00acb6]/20"
                  />
                  <span className="text-[0.875rem] text-[#737373]">Remember me</span>
                </label>
                <a href="#" className="text-[0.875rem] font-semibold text-[#e61844] hover:text-[#cf0627] transition-colors">
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-[#e61844] hover:bg-[#cf0627] text-white font-semibold rounded transition-colors duration-150 disabled:opacity-50 text-[1rem] border border-[#e61844] hover:border-[#cf0627]"
              >
                {loading ? "Signing in..." : "Sign In"}
              </button>

              <div className="mt-4 p-4 bg-[#f4f4f4] border border-[#dedede] rounded">
                <p className="text-[0.875rem] text-[#737373] text-center leading-relaxed">
                  <span className="font-semibold text-[#333]">Parents:</span> Your psychologist will send you a magic link via email to set up your account.
                </p>
              </div>
            </form>

            <footer className="mt-12 text-center">
              <div className="flex justify-center gap-6 text-[0.6875rem] font-semibold uppercase tracking-[0.15em] text-[#737373]">
                <a href="#" className="hover:text-[#e61844] transition-colors">Documentation</a>
                <a href="#" className="hover:text-[#e61844] transition-colors">Support</a>
                <a href="#" className="hover:text-[#e61844] transition-colors">Privacy</a>
              </div>
              <div className="mt-6 text-[0.75rem] text-[#737373]">
                © 2026 The Ed Psych Practice. All clinical data encrypted.
              </div>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}
