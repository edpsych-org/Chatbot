"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

/**
 * Sticky top bar with The Ed Psych Practice brand, the signed-in user's
 * name/email, and a sign-out button.
 *
 * All sizes are pinned in explicit pixels so the bar is immune to the
 * AccessibilityMenu's html font-scale — renders identically at 100 /
 * 115 / 130 / 150 %. That matches the admin dashboard's pinned header
 * and gives a consistent branded chrome across every authenticated
 * admin/psychologist page.
 *
 * Optional `subtitle` slot (e.g. "Reports Workspace") appears beneath
 * the brand wordmark. Optional `backHref` adds a ◀ button at the left.
 */
export default function BrandTopBar({
  subtitle,
  backHref,
  backLabel = "Back",
}: {
  subtitle?: string;
  backHref?: string;
  backLabel?: string;
}) {
  const router = useRouter();
  const [user, setUser] = useState<{
    full_name?: string;
    email?: string;
  } | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("user");
      if (raw) setUser(JSON.parse(raw));
    } catch {
      /* ignore */
    }
  }, []);

  const handleLogout = () => {
    try {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
    } catch {
      /* ignore */
    }
    router.push("/login");
  };

  return (
    <header className="bg-white backdrop-blur-xl border-b border-[#dedede] sticky top-0 z-40">
      <div
        className="max-w-[1400px] mx-auto"
        style={{ paddingLeft: "21px", paddingRight: "21px" }}
      >
        <div className="flex items-center justify-between" style={{ height: "73px" }}>
          <div className="flex items-center" style={{ gap: "16px" }}>
            {backHref && (
              <button
                type="button"
                onClick={() => router.push(backHref)}
                className="rounded-[8px] bg-[#f4f4f4] hover:bg-[#eeeeee] text-[#333] flex items-center justify-center transition-colors"
                style={{ width: "42px", height: "42px" }}
                aria-label={backLabel}
              >
                <svg
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  style={{ width: "21px", height: "21px" }}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
            )}
            <div
              className="rounded-[8px] bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center"
              style={{ width: "42px", height: "42px" }}
            >
              <svg
                style={{ width: "21px", height: "21px" }}
                className="text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div>
              <h1
                className="font-serif font-bold text-[#0c888e] leading-none"
                style={{ fontSize: "23px" }}
              >
                The Ed Psych Practice
              </h1>
              {subtitle && (
                <p
                  className="font-medium text-[#737373] tracking-widest uppercase"
                  style={{ fontSize: "12px", marginTop: "2px" }}
                >
                  {subtitle}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center" style={{ gap: "16px" }}>
            {user && (
              <div className="hidden md:block text-right">
                <p
                  className="font-medium text-[#333] leading-none"
                  style={{ fontSize: "18px" }}
                >
                  {user.full_name || user.email}
                </p>
                {user.email && (
                  <p
                    className="text-[#737373]"
                    style={{ fontSize: "14px", marginTop: "3px" }}
                  >
                    {user.email}
                  </p>
                )}
              </div>
            )}
            <div
              className="rounded-full bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white font-bold"
              style={{ width: "42px", height: "42px", fontSize: "14px" }}
            >
              {(user?.full_name || user?.email || "U").charAt(0).toUpperCase()}
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="font-medium text-[#737373] hover:text-[#e61844] transition-colors"
              style={{ fontSize: "16px" }}
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
