"use client";

import Link from "next/link";

const ABOUT_LINKS = [
  { label: "About Us", href: "/about" },
  { label: "Our Founder", href: "/founder" },
  { label: "Career", href: "/career" },
  { label: "Consultants", href: "/consultants" },
  { label: "Contact Us", href: "/contact" },
  { label: "Terms and Conditions", href: "/terms-and-conditions" },
];

const SOCIALS = [
  { label: "Facebook", href: "https://www.facebook.com/theedpsych/", icon: "f" },
  { label: "Instagram", href: "https://www.instagram.com/theedpsych/", icon: "ig" },
  { label: "Twitter / X", href: "https://twitter.com/EdPsychPractice", icon: "x" },
  { label: "LinkedIn", href: "https://www.linkedin.com/company/the-ed-psych-practice/", icon: "in" },
];

const CERTIFICATIONS = ["bps", "hcpc", "rcot", "rcslt", "baat", "bamt", "patoss"];

export default function SiteFooter() {
  return (
    <footer className="bg-slate-900 text-slate-200 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          <div>
            <h4 className="text-white font-bold mb-4 text-lg">About Practice</h4>
            <ul className="space-y-2 text-sm">
              {ABOUT_LINKS.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="hover:text-primary transition-colors">
                    — {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-bold mb-4 text-lg">Contact Us</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="tel:+447833447356" className="hover:text-primary">
                  +44 (0) 78 3344 7356
                </a>
              </li>
              <li>
                <a href="mailto:office@theedpsych.com" className="hover:text-primary">
                  office@theedpsych.com
                </a>
              </li>
            </ul>
            <h4 className="text-white font-bold mb-3 mt-6 text-lg">Follow Us</h4>
            <div className="flex gap-3">
              {SOCIALS.map((s) => (
                <a
                  key={s.href}
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={s.label}
                  title={s.label}
                  className="w-9 h-9 rounded-full bg-white/10 hover:bg-primary flex items-center justify-center text-xs font-bold transition-colors"
                >
                  {s.icon}
                </a>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-white font-bold mb-4 text-lg">Subscribe Newsletter</h4>
            <p className="text-sm text-slate-300 mb-4">
              Get subscribed to stay updated on our latest services. Never miss even a single update from our end.
            </p>
            <form
              className="flex flex-col sm:flex-row gap-2"
              onSubmit={(e) => e.preventDefault()}
            >
              <input
                type="email"
                required
                placeholder="E-mail Address"
                className="flex-1 px-3 py-2 rounded-md bg-white/10 border border-white/20 text-white placeholder-slate-400 focus:outline-none focus:border-primary"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-accent hover:bg-red-600 text-white font-bold rounded-md text-sm"
              >
                SUBSCRIBE
              </button>
            </form>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-white/10">
          <p className="text-center text-slate-400 text-xs mb-4">Practitioners registered with:</p>
          <div className="flex flex-wrap justify-center items-center gap-6">
            {CERTIFICATIONS.map((c) => (
              <img
                key={c}
                src={`/images/certified/${c}.png`}
                alt={`${c.toUpperCase()} certification`}
                className="h-10 sm:h-12 w-auto bg-white rounded-md p-1 opacity-90"
              />
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-white/10 py-4 text-center text-xs text-slate-400">
        Copyright © {new Date().getFullYear()} The Ed Psych Practice. All Rights Reserved.
      </div>
    </footer>
  );
}
