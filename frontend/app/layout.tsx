import type { Metadata } from "next";
import Script from "next/script";
import { Average, Nunito } from "next/font/google";
import AccessibilityMenu from "@/components/AccessibilityMenu";
import "./globals.css";

// Ed Psych Practice fonts — mirror https://www.theedpsych.com
// Average (serif) for headings, Nunito (sans) for body.
// Loaded via next/font for zero-CLS, self-hosted, and automatically optimized.
const average = Average({
  subsets: ["latin"],
  weight: "400",
  display: "swap",
  variable: "--font-average",
});

const nunito = Nunito({
  subsets: ["latin"],
  weight: ["300", "400", "600", "700", "800"],
  display: "swap",
  variable: "--font-nunito",
});

export const metadata: Metadata = {
  title: "The EdPsych Practice | Educational Psychology Platform",
  description: "Educational psychology assessment and report generation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`light ${average.variable} ${nunito.variable}`}>
      <head>
        {/*
          Reads saved font-scale from localStorage and applies it to <html>
          BEFORE React hydration. Prevents a flash where a 150% user
          briefly sees the 100% layout on first paint.
        */}
        <Script
          src="/font-scale-boot.js"
          strategy="beforeInteractive"
        />
      </head>
      <body>
        <div className="noise-overlay" />
        {children}
        <AccessibilityMenu />
      </body>
    </html>
  );
}
