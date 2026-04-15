"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const NAV = [
  { label: "Home", href: "/" },
  { label: "About", href: "/about" },
  { label: "Services", href: "/services" },
  { label: "Schools", href: "/schools" },
  { label: "Consultants", href: "/consultants" },
  { label: "Contact", href: "/contact" },
  { label: "FAQs", href: "/faq" },
];

const EXTERNAL = [
  { label: "Autism", href: "https://www.support4autism.com/" },
  { label: "OT Speech", href: "https://www.otspeechtherapy.com/" },
];

function dashboardHrefFor(role?: string): string {
  const r = (role || "").toUpperCase();
  if (r === "PSYCHOLOGIST") return "/psychologist/dashboard";
  if (r === "ADMIN") return "/admin/dashboard";
  return "/dashboard";
}

export default function SiteHeader() {
  const [dashboardHref, setDashboardHref] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) return;
      const raw = localStorage.getItem("user");
      const role = raw ? JSON.parse(raw)?.role : undefined;
      setDashboardHref(dashboardHrefFor(role));
    } catch {
      /* ignore */
    }
  }, []);

  return (
    <header className="site-header-pinned sticky top-0 z-40 bg-white shadow-sm border-b border-slate-200">
      {/* brand strip */}
      <div className="bg-primary text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
          <Link href="/" className="flex items-baseline gap-3 min-w-0">
            <span className="brand-wordmark text-lg sm:text-xl font-bold truncate">
              The Ed Psych Practice
            </span>
            <em className="hidden md:inline text-xs sm:text-sm text-white/85 not-italic">
              An Independent Practice in Central London
            </em>
          </Link>
          <a
            href="tel:+447833447356"
            className="text-sm font-semibold whitespace-nowrap hover:underline"
          >
            +44 (0) 78 3344 7356
          </a>
        </div>
      </div>

      {/* nav row */}
      <div className="bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <nav className="hidden md:flex items-center gap-1">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="px-3 py-2 text-sm font-semibold text-slate-700 hover:text-primary hover:bg-teal-50 rounded-md transition-colors"
                >
                  {item.label}
                </Link>
              ))}
              {EXTERNAL.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-2 text-sm font-semibold text-slate-500 hover:text-primary rounded-md"
                >
                  {item.label} ↗
                </a>
              ))}
            </nav>

            <div className="flex items-center gap-2">
              {dashboardHref ? (
                <Link
                  href={dashboardHref}
                  className="ed-btn-primary px-4 py-2 text-sm rounded-lg"
                >
                  Dashboard
                </Link>
              ) : (
                <Link
                  href="/login"
                  className="ed-btn-primary px-4 py-2 text-sm rounded-lg"
                >
                  Login
                </Link>
              )}

              <button
                className="md:hidden p-2 rounded-lg hover:bg-slate-100"
                aria-label="Open menu"
                onClick={() => setMenuOpen((o) => !o)}
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>

          {menuOpen && (
            <div className="md:hidden pb-4 pt-2 border-t border-slate-100">
              <nav className="flex flex-col gap-1">
                {NAV.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMenuOpen(false)}
                    className="px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-teal-50 rounded-md"
                  >
                    {item.label}
                  </Link>
                ))}
                {EXTERNAL.map((item) => (
                  <a
                    key={item.href}
                    href={item.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-2 text-sm font-semibold text-slate-500 rounded-md"
                  >
                    {item.label} ↗
                  </a>
                ))}
              </nav>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
