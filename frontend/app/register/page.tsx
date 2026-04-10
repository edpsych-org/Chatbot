"use client";

import Link from "next/link";

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Top teal nav — matches theedpsych.com */}
      <div className="ed-nav w-full py-3 px-6">
        <span className="text-white font-serif text-xl tracking-wide">The Ed Psych Practice</span>
      </div>

      <div className="flex-1 flex items-center justify-center px-4 py-12 ed-hero relative overflow-hidden">
        {/* Decorative cherry-blossom corners */}
        <img
          src="/images/cherry-tree.png"
          alt=""
          aria-hidden="true"
          className="absolute top-0 left-0 w-[280px] opacity-30 pointer-events-none select-none"
        />
        <img
          src="/images/cherry-tree.png"
          alt=""
          aria-hidden="true"
          className="absolute bottom-0 right-0 w-[240px] opacity-25 pointer-events-none select-none transform scale-x-[-1]"
        />
        <div className="max-w-lg w-full relative z-10">
          {/* Branding */}
          <div className="text-center mb-8">
            <h1 className="brand-wordmark mb-2">The Ed Psych Practice</h1>
            <p className="brand-tagline">An Independent Practice in Central London</p>
          </div>

          {/* Main Card */}
          <div className="ed-card bg-white p-8 sm:p-10">
            <h1 className="font-serif text-[1.875rem] text-[#333] mb-3 text-center">
              Parent <span className="text-[#00a1aa]">Registration</span>
            </h1>

            <div className="w-16 h-[2px] bg-[#00acb6] mx-auto mb-6" />

            <p className="text-[#737373] text-[1rem] leading-[1.8] text-center mb-8">
              Parent accounts are created by your assigned educational psychologist.
              When an assessment is assigned to your child, you&apos;ll receive a
              secure invitation link via email.
            </p>

            {/* How it works */}
            <div className="mb-8">
              <h2 className="text-[0.75rem] font-bold uppercase tracking-wider text-[#00acb6] mb-4 text-center">
                How it works
              </h2>
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  <div className="w-9 h-9 rounded-full bg-[#00acb6] text-white flex items-center justify-center text-[0.9375rem] font-bold flex-shrink-0 font-serif">
                    1
                  </div>
                  <p className="text-[0.9375rem] text-[#333] pt-1.5">
                    Your psychologist creates a profile for your child
                  </p>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-9 h-9 rounded-full bg-[#00acb6] text-white flex items-center justify-center text-[0.9375rem] font-bold flex-shrink-0 font-serif">
                    2
                  </div>
                  <p className="text-[0.9375rem] text-[#333] pt-1.5">
                    You receive a secure magic link via email
                  </p>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-9 h-9 rounded-full bg-[#00acb6] text-white flex items-center justify-center text-[0.9375rem] font-bold flex-shrink-0 font-serif">
                    3
                  </div>
                  <p className="text-[0.9375rem] text-[#333] pt-1.5">
                    Click the link to set up your password and access the assessment
                  </p>
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="relative py-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#dedede]" />
              </div>
              <div className="relative flex justify-center text-[0.6875rem] uppercase tracking-[0.2em] font-semibold text-[#737373]">
                <span className="bg-white px-4">Already have an account?</span>
              </div>
            </div>

            <Link
              href="/login"
              className="block w-full py-3 bg-[#e61844] hover:bg-[#cf0627] text-white font-semibold rounded transition-colors text-[1rem] text-center mt-4"
            >
              Login
            </Link>

            <p className="text-[0.8125rem] text-[#737373] text-center mt-6">
              Didn&apos;t receive an invitation? Contact your psychologist directly.
            </p>
          </div>

          {/* Footer */}
          <footer className="mt-10 text-center">
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
      </div>
    </div>
  );
}
