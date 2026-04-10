"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Floating accessibility menu — lets users enlarge text for readability.
 *
 * Strategy: sets `data-font-scale` on the <html> element (100/115/130/150).
 * CSS in globals.css defines `html[data-font-scale="..."] { font-size: ... }`,
 * so every rem-based Tailwind class (text-sm, p-4, gap-6, etc.) scales
 * proportionally. Layout stays stable because spacing grows with text.
 *
 * Persists to localStorage. The widget itself uses fixed px sizes (via
 * inline styles) so it does not balloon when the user picks 150%.
 */
const LEVELS = [
  { value: "100", label: "A", description: "Normal" },
  { value: "115", label: "A", description: "Large" },
  { value: "130", label: "A", description: "Larger" },
  { value: "150", label: "A", description: "Largest" },
] as const;

type Level = (typeof LEVELS)[number]["value"];

export default function AccessibilityMenu() {
  const [open, setOpen] = useState(false);
  const [scale, setScale] = useState<Level>("100");
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Hydrate from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("fontScale") as Level | null;
      if (saved && LEVELS.some((l) => l.value === saved)) {
        setScale(saved);
      }
    } catch {
      // localStorage unavailable — silent no-op
    }
  }, []);

  // Close on outside click or Esc
  useEffect(() => {
    if (!open) return;

    const onClick = (e: MouseEvent) => {
      if (
        panelRef.current &&
        !panelRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const apply = (level: Level) => {
    setScale(level);
    try {
      localStorage.setItem("fontScale", level);
    } catch {
      // ignore
    }
    if (level === "100") {
      document.documentElement.removeAttribute("data-font-scale");
    } else {
      document.documentElement.setAttribute("data-font-scale", level);
    }
  };

  return (
    <div
      className="fixed bottom-4 right-4 z-[60] flex flex-col items-end"
      // fixed pixel sizes so the widget does not scale with its own setting
      style={{ fontSize: "14px", lineHeight: 1.4 }}
    >
      {/* Menu panel */}
      {open && (
        <div
          ref={panelRef}
          role="menu"
          aria-label="Text size options"
          className="mb-2 rounded-lg border border-[#dedede] bg-white shadow-lg overflow-hidden animate-fade-in"
          style={{ minWidth: "200px" }}
        >
          <div
            className="px-4 py-2 border-b border-[#dedede] bg-[#f4f4f4] font-semibold text-[#333]"
            style={{ fontSize: "13px" }}
          >
            Text size
          </div>
          <div className="flex flex-col">
            {LEVELS.map((l, idx) => {
              const isActive = scale === l.value;
              return (
                <button
                  key={l.value}
                  role="menuitemradio"
                  aria-checked={isActive}
                  onClick={() => apply(l.value)}
                  className={`flex items-center justify-between px-4 py-2.5 text-left transition-colors border-t border-[#eeeeee] first:border-t-0 ${
                    isActive
                      ? "bg-[#e6f7f8] text-[#0c888e] font-semibold"
                      : "hover:bg-[#f4f4f4] text-[#333]"
                  }`}
                  style={{ fontSize: "13px" }}
                >
                  <span className="flex items-baseline gap-2">
                    <span
                      aria-hidden="true"
                      style={{
                        fontFamily: "var(--font-average), Georgia, serif",
                        fontSize:
                          idx === 0
                            ? "14px"
                            : idx === 1
                              ? "16px"
                              : idx === 2
                                ? "18px"
                                : "20px",
                        color: isActive ? "#0c888e" : "#737373",
                      }}
                    >
                      {l.label}
                    </span>
                    <span>{l.description}</span>
                  </span>
                  <span style={{ fontSize: "11px", color: "#737373" }}>
                    {l.value}%
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Trigger button */}
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="Adjust text size for accessibility"
        aria-haspopup="menu"
        aria-expanded={open}
        className="rounded-full bg-[#00acb6] hover:bg-[#0c888e] text-white shadow-lg transition-colors flex items-center gap-2 border border-[#00acb6] hover:border-[#0c888e]"
        style={{
          padding: "10px 16px",
          fontSize: "14px",
          fontWeight: 600,
        }}
      >
        <span
          aria-hidden="true"
          style={{
            fontFamily: "var(--font-average), Georgia, serif",
            fontSize: "18px",
            lineHeight: 1,
          }}
        >
          Aa
        </span>
        <span className="hidden sm:inline">Text size</span>
      </button>
    </div>
  );
}
