/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Ed Psych Practice palette — https://www.theedpsych.com
        // Teal for navigation / brand chrome, red for CTAs, green for service bands.
        background: "#ffffff",
        surface: "#f4f4f4",
        "surface-container-low": "#eeeeee",
        "surface-container-lowest": "#ffffff",

        // primary = brand teal (navigation, links-on-dark, logo)
        primary: "#00acb6",
        "primary-dark": "#0c888e",
        "primary-deep": "#0f8b92",
        "primary-container": "#e6f7f8",
        "on-primary-container": "#0c888e",

        // accent = red CTA (buttons, links)
        accent: "#e61844",
        "accent-hover": "#cf0627",
        "accent-border": "#b81336",
        secondary: "#e61844",

        // service band green (used on info sections)
        service: "#86b454",
        "service-dark": "#597737",
        "service-alt": "#78a547",
        "service-alt-dark": "#4a741b",

        // text
        "on-background": "#333333",
        "on-surface": "#333333",
        muted: "#737373",

        // lines
        outline: "#dee2e6",
        "outline-variant": "#e5e5e5",
        "outline-dashed": "#cccccc",

        // Ed Psych direct names (for explicit usage)
        "brand-teal": "#00acb6",
        "brand-teal-dark": "#0c888e",
        "brand-red": "#e61844",
        "brand-red-hover": "#cf0627",
        "brand-green": "#86b454",
        "brand-green-dark": "#597737",
        "brand-hero": "#eeeeee",
        "brand-section": "#f4f4f4",
        "brand-footer": "#efefef",
      },
      fontFamily: {
        // Average (serif) for headings; Nunito (sans) for body — mirror theedpsych.com.
        // Variables are injected by next/font in app/layout.tsx.
        headline: ["var(--font-average)", "Georgia", "serif"],
        serif: ["var(--font-average)", "Georgia", "serif"],
        body: ["var(--font-nunito)", "system-ui", "sans-serif"],
        label: ["var(--font-nunito)", "system-ui", "sans-serif"],
        sans: ["var(--font-nunito)", "system-ui", "sans-serif"],
      },
      fontSize: {
        // Compressed heading scale to match Ed Psych document-like tone.
        // Sizes in rem so they scale with the html font-scale accessibility setting.
        "brand-logo": ["2.25rem", { lineHeight: "1.2" }], // 36px @ 100%
        "brand-h1": ["1.875rem", { lineHeight: "1.3" }],  // 30px
        "brand-h2": ["1.5rem", { lineHeight: "1.3" }],    // 24px
        "brand-h3": ["1.375rem", { lineHeight: "1.35" }], // 22px
        "brand-h5": ["1.25rem", { lineHeight: "1.4" }],   // 20px
        "brand-body": ["1.125rem", { lineHeight: "1.8" }],// 18px
      },
      borderRadius: {
        // Flat 4px base like Bootstrap-era, but keep larger utility classes for cards
        DEFAULT: "4px",
        sm: "2px",
        md: "4px",
        lg: "6px",
        xl: "8px",
        "2xl": "12px",
        full: "9999px",
      },
      boxShadow: {
        // Softer shadows — Ed Psych is mostly flat
        card: "0 1px 2px rgba(0,0,0,0.04)",
        "card-hover": "0 2px 6px rgba(0,0,0,0.06)",
      },
    },
  },
  plugins: [],
};
