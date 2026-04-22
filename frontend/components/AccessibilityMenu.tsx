"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Draggable accessibility menu — lets users enlarge text for readability.
 *
 * Sets `data-font-scale` on the <html> element (100/115/130/150).
 * CSS in globals.css defines `html[data-font-scale="..."] { font-size: ... }`,
 * so every rem-based Tailwind class scales proportionally.
 *
 * The button floats and can be dragged anywhere in the viewport (mouse or
 * touch). Position persists to localStorage alongside the scale setting.
 */
const LEVELS = [
  { value: "100", label: "A", description: "Normal" },
  { value: "115", label: "A", description: "Large" },
  { value: "130", label: "A", description: "Larger" },
  { value: "150", label: "A", description: "Largest" },
] as const;

type Level = (typeof LEVELS)[number]["value"];

const BTN_WIDTH = 130;  // approx, only used for initial clamp — real size measured at runtime
const BTN_HEIGHT = 44;
const POS_KEY = "fontScaleBtnPos";
const DRAG_THRESHOLD = 5; // px — movement below this is treated as a click

export default function AccessibilityMenu() {
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);
  const [scale, setScale] = useState<Level>("100");
  const [pos, setPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [panelUp, setPanelUp] = useState(true);

  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragState = useRef<{
    startX: number;
    startY: number;
    offsetX: number;
    offsetY: number;
    moved: boolean;
  } | null>(null);

  const clampPos = useCallback((x: number, y: number) => {
    const w = containerRef.current?.offsetWidth ?? BTN_WIDTH;
    const h = containerRef.current?.offsetHeight ?? BTN_HEIGHT;
    const maxX = Math.max(0, window.innerWidth - w - 8);
    const maxY = Math.max(0, window.innerHeight - h - 8);
    return {
      x: Math.min(Math.max(8, x), maxX),
      y: Math.min(Math.max(8, y), maxY),
    };
  }, []);

  // Hydrate scale + position on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("fontScale") as Level | null;
      if (saved && LEVELS.some((l) => l.value === saved)) {
        setScale(saved);
      }
    } catch { /* ignore */ }

    try {
      const raw = localStorage.getItem(POS_KEY);
      if (raw) {
        const p = JSON.parse(raw);
        if (typeof p?.x === "number" && typeof p?.y === "number") {
          setPos(clampPos(p.x, p.y));
          setMounted(true);
          return;
        }
      }
    } catch { /* ignore */ }

    // Default: bottom-right
    setPos({
      x: window.innerWidth - BTN_WIDTH - 16,
      y: window.innerHeight - BTN_HEIGHT - 16,
    });
    setMounted(true);
  }, [clampPos]);

  // Re-clamp on viewport resize so button never leaves the screen
  useEffect(() => {
    const onResize = () => setPos((p) => clampPos(p.x, p.y));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [clampPos]);

  // Decide whether panel opens above or below the button
  useEffect(() => {
    if (!open || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    setPanelUp(spaceBelow < 280);
  }, [open, pos]);

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
    try { localStorage.setItem("fontScale", level); } catch { /* ignore */ }
    if (level === "100") {
      document.documentElement.removeAttribute("data-font-scale");
    } else {
      document.documentElement.setAttribute("data-font-scale", level);
    }
  };

  const onPointerDown = (e: React.PointerEvent<HTMLButtonElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    dragState.current = {
      startX: e.clientX,
      startY: e.clientY,
      offsetX: e.clientX - rect.left,
      offsetY: e.clientY - rect.top,
      moved: false,
    };
    (e.target as Element).setPointerCapture(e.pointerId);
    setDragging(true);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLButtonElement>) => {
    const s = dragState.current;
    if (!s) return;
    const dx = e.clientX - s.startX;
    const dy = e.clientY - s.startY;
    if (!s.moved && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
    s.moved = true;
    setOpen(false); // close panel while dragging
    setPos(clampPos(e.clientX - s.offsetX, e.clientY - s.offsetY));
  };

  const onPointerUp = (e: React.PointerEvent<HTMLButtonElement>) => {
    const s = dragState.current;
    (e.target as Element).releasePointerCapture(e.pointerId);
    setDragging(false);
    dragState.current = null;
    if (!s) return;
    if (s.moved) {
      // Persist new position
      try {
        localStorage.setItem(POS_KEY, JSON.stringify(pos));
      } catch { /* ignore */ }
    } else {
      // Treat as click — toggle panel
      setOpen((o) => !o);
    }
  };

  // Keep localStorage in sync when pos changes after a drag completes
  useEffect(() => {
    if (dragging) return;
    try { localStorage.setItem(POS_KEY, JSON.stringify(pos)); } catch { /* ignore */ }
  }, [pos, dragging]);

  if (!mounted) return null;

  return (
    <div
      ref={containerRef}
      className="fixed z-[60] flex flex-col items-end"
      style={{
        left: `${pos.x}px`,
        top: `${pos.y}px`,
        fontSize: "14px",
        lineHeight: 1.4,
        touchAction: "none",
        userSelect: "none",
      }}
    >
      {open && panelUp && (
        <AccessibilityPanel
          panelRef={panelRef}
          scale={scale}
          apply={apply}
          position="above"
        />
      )}

      <button
        ref={triggerRef}
        type="button"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        aria-label="Adjust text size for accessibility (drag to move)"
        aria-haspopup="menu"
        aria-expanded={open}
        className={`rounded-full bg-[#00acb6] hover:bg-[#0c888e] text-white shadow-lg transition-colors flex items-center gap-2 border border-[#00acb6] hover:border-[#0c888e] ${
          dragging ? "cursor-grabbing" : "cursor-grab"
        }`}
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

      {open && !panelUp && (
        <AccessibilityPanel
          panelRef={panelRef}
          scale={scale}
          apply={apply}
          position="below"
        />
      )}
    </div>
  );
}

function AccessibilityPanel({
  panelRef,
  scale,
  apply,
  position,
}: {
  panelRef: React.RefObject<HTMLDivElement>;
  scale: Level;
  apply: (level: Level) => void;
  position: "above" | "below";
}) {
  return (
    <div
      ref={panelRef}
      role="menu"
      aria-label="Text size options"
      className={`rounded-lg border border-[#dedede] bg-white shadow-lg overflow-hidden animate-fade-in ${
        position === "above" ? "mb-2" : "mt-2"
      }`}
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
                      idx === 0 ? "14px" : idx === 1 ? "16px" : idx === 2 ? "18px" : "20px",
                    color: isActive ? "#0c888e" : "#737373",
                  }}
                >
                  {l.label}
                </span>
                <span>{l.description}</span>
              </span>
              <span style={{ fontSize: "11px", color: "#737373" }}>{l.value}%</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
