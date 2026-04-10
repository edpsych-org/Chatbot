"use client";

import { Fragment, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { API_BASE } from "@/lib/api";
import ConfirmModal from "@/components/ConfirmModal";
import { useConfirm } from "@/hooks/useConfirm";

interface MarkdownEditorProps {
  reportId: string | null;
  initialContent: string;
  onContentChange?: (content: string) => void;
}

type SaveStatus = "saved" | "unsaved" | "saving" | "error";

/**
 * Minimal markdown renderer that produces React nodes directly (no
 * dangerouslySetInnerHTML, no injection risk). Supports:
 *   # / ## / ### headers
 *   **bold**, *italic*
 *   - bullet lists
 *   blank-line paragraphs, soft line breaks
 */
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  // Tokenize **bold** and *italic* without regex-replace-into-HTML.
  const nodes: ReactNode[] = [];
  let remaining = text;
  let i = 0;

  while (remaining.length > 0) {
    const boldStart = remaining.indexOf("**");
    const italicStart = remaining.indexOf("*");

    // Bold takes priority if it's the same position
    if (boldStart !== -1 && (italicStart === -1 || boldStart <= italicStart)) {
      if (boldStart > 0) {
        nodes.push(<Fragment key={`${keyPrefix}-t${i++}`}>{remaining.slice(0, boldStart)}</Fragment>);
      }
      const after = remaining.slice(boldStart + 2);
      const close = after.indexOf("**");
      if (close === -1) {
        nodes.push(<Fragment key={`${keyPrefix}-t${i++}`}>{remaining.slice(boldStart)}</Fragment>);
        break;
      }
      nodes.push(
        <strong key={`${keyPrefix}-b${i++}`} className="font-semibold text-slate-900">
          {after.slice(0, close)}
        </strong>
      );
      remaining = after.slice(close + 2);
      continue;
    }

    if (italicStart !== -1) {
      if (italicStart > 0) {
        nodes.push(<Fragment key={`${keyPrefix}-t${i++}`}>{remaining.slice(0, italicStart)}</Fragment>);
      }
      const after = remaining.slice(italicStart + 1);
      const close = after.indexOf("*");
      if (close === -1) {
        nodes.push(<Fragment key={`${keyPrefix}-t${i++}`}>{remaining.slice(italicStart)}</Fragment>);
        break;
      }
      nodes.push(
        <em key={`${keyPrefix}-i${i++}`} className="italic">
          {after.slice(0, close)}
        </em>
      );
      remaining = after.slice(close + 1);
      continue;
    }

    nodes.push(<Fragment key={`${keyPrefix}-t${i++}`}>{remaining}</Fragment>);
    break;
  }
  return nodes;
}

function renderMarkdown(md: string): ReactNode {
  if (!md || md.trim() === "") {
    return <p className="text-slate-400 italic">Nothing to preview yet.</p>;
  }

  const lines = md.split(/\r?\n/);
  const blocks: ReactNode[] = [];
  let paragraphBuf: string[] = [];
  let listBuf: string[] = [];
  let blockKey = 0;

  const flushParagraph = () => {
    if (paragraphBuf.length > 0) {
      const key = `p-${blockKey++}`;
      blocks.push(
        <p key={key} className="mb-3 text-slate-700 leading-relaxed">
          {paragraphBuf.map((ln, idx) => (
            <Fragment key={`${key}-ln${idx}`}>
              {idx > 0 && <br />}
              {renderInline(ln, `${key}-ln${idx}`)}
            </Fragment>
          ))}
        </p>
      );
      paragraphBuf = [];
    }
  };

  const flushList = () => {
    if (listBuf.length > 0) {
      const key = `ul-${blockKey++}`;
      blocks.push(
        <ul key={key} className="list-disc pl-6 mb-3 space-y-1 text-slate-700">
          {listBuf.map((item, idx) => (
            <li key={`${key}-li${idx}`}>{renderInline(item, `${key}-li${idx}`)}</li>
          ))}
        </ul>
      );
      listBuf = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.trim() === "") {
      flushParagraph();
      flushList();
      continue;
    }

    const h3 = line.match(/^###\s+(.*)$/);
    const h2 = line.match(/^##\s+(.*)$/);
    const h1 = line.match(/^#\s+(.*)$/);
    const li = line.match(/^[-*]\s+(.*)$/);

    if (h1) {
      flushParagraph();
      flushList();
      const key = `h1-${blockKey++}`;
      blocks.push(
        <h1 key={key} className="text-2xl font-extrabold text-slate-900 mt-6 mb-3">
          {renderInline(h1[1], key)}
        </h1>
      );
    } else if (h2) {
      flushParagraph();
      flushList();
      const key = `h2-${blockKey++}`;
      blocks.push(
        <h2 key={key} className="text-xl font-bold text-slate-900 mt-5 mb-2">
          {renderInline(h2[1], key)}
        </h2>
      );
    } else if (h3) {
      flushParagraph();
      flushList();
      const key = `h3-${blockKey++}`;
      blocks.push(
        <h3 key={key} className="text-lg font-bold text-slate-800 mt-4 mb-2">
          {renderInline(h3[1], key)}
        </h3>
      );
    } else if (li) {
      flushParagraph();
      listBuf.push(li[1]);
    } else {
      flushList();
      paragraphBuf.push(line);
    }
  }

  flushParagraph();
  flushList();
  return <>{blocks}</>;
}

function formatRelative(date: Date | null): string {
  if (!date) return "";
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return date.toLocaleDateString();
}

export default function MarkdownEditor({
  reportId,
  initialContent,
  onContentChange,
}: MarkdownEditorProps) {
  const [mode, setMode] = useState<"edit" | "preview">("edit");
  const [content, setContent] = useState(initialContent);
  const [savedBaseline, setSavedBaseline] = useState(initialContent);
  const [status, setStatus] = useState<SaveStatus>("saved");
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [, forceTick] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const { confirm, confirmProps } = useConfirm();

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestContentRef = useRef(content);

  // Reset editor when parent swaps in a new report or new initial content
  useEffect(() => {
    setContent(initialContent);
    setSavedBaseline(initialContent);
    latestContentRef.current = initialContent;
    setStatus("saved");
    setLastSaved(null);
    setErrorMsg(null);
  }, [reportId, initialContent]);

  // Tick every 30s to refresh the "X ago" label
  useEffect(() => {
    const t = setInterval(() => forceTick((v) => v + 1), 30000);
    return () => clearInterval(t);
  }, []);

  const hasChanges = content !== savedBaseline;

  const doSave = useCallback(
    async (value: string) => {
      if (!reportId) return;
      const token = localStorage.getItem("access_token");
      if (!token) return;

      setStatus("saving");
      setErrorMsg(null);
      try {
        const res = await fetch(`${API_BASE}/psychologist-reports/reports/${reportId}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ content_markdown: value }),
        });
        if (!res.ok) {
          throw new Error(`Save failed (${res.status})`);
        }
        setSavedBaseline(value);
        if (latestContentRef.current === value) {
          setStatus("saved");
        } else {
          setStatus("unsaved");
        }
        setLastSaved(new Date());
      } catch (err) {
        console.error("Autosave failed:", err);
        setStatus("error");
        setErrorMsg(err instanceof Error ? err.message : "Save failed");
      }
    },
    [reportId]
  );

  const handleChange = (next: string) => {
    setContent(next);
    latestContentRef.current = next;
    onContentChange?.(next);

    if (!reportId) return;
    if (next === savedBaseline) {
      setStatus("saved");
      if (debounceRef.current) clearTimeout(debounceRef.current);
      return;
    }
    setStatus("unsaved");

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      doSave(next);
    }, 1500);
  };

  const handleManualSave = () => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    doSave(content);
  };

  const handleDiscard = async () => {
    if (!hasChanges) return;
    const ok = await confirm(
      "Discard all unsaved changes and revert to the last saved version?",
      { title: "Discard Changes", confirmLabel: "Discard", variant: "danger" }
    );
    if (!ok) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setContent(savedBaseline);
    latestContentRef.current = savedBaseline;
    onContentChange?.(savedBaseline);
    setStatus("saved");
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  const previewNode = useMemo(() => renderMarkdown(content), [content]);

  const statusDisplay = () => {
    if (status === "saving") {
      return (
        <span className="flex items-center gap-2 text-xs font-medium text-teal-600">
          <span className="w-3 h-3 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          Saving...
        </span>
      );
    }
    if (status === "unsaved") {
      return (
        <span className="flex items-center gap-2 text-xs font-medium text-amber-600">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          Unsaved changes
        </span>
      );
    }
    if (status === "error") {
      return (
        <span className="flex items-center gap-2 text-xs font-medium text-red-600">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          {errorMsg || "Save failed"}
        </span>
      );
    }
    return (
      <span className="flex items-center gap-2 text-xs font-medium text-emerald-600">
        <span className="w-2 h-2 rounded-full bg-emerald-500" />
        {lastSaved ? `Saved ${formatRelative(lastSaved)}` : "Saved"}
      </span>
    );
  };

  return (
    <div className="w-full">
      <ConfirmModal {...confirmProps} />
      {/* Tabs + status bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="inline-flex rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setMode("edit")}
            className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
              mode === "edit"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => setMode("preview")}
            className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
              mode === "preview"
                ? "bg-white text-slate-900 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Preview
          </button>
        </div>
        <div className="flex items-center gap-3">{statusDisplay()}</div>
      </div>

      {/* Editor or preview */}
      {mode === "edit" ? (
        <textarea
          value={content}
          onChange={(e) => handleChange(e.target.value)}
          className="w-full min-h-[400px] p-4 border border-slate-200 rounded-xl bg-white text-slate-800 font-mono text-sm leading-relaxed resize-y focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all"
          placeholder="# Heading&#10;&#10;Write your report in markdown..."
          spellCheck
        />
      ) : (
        <div className="w-full min-h-[400px] p-5 border border-slate-200 rounded-xl bg-white overflow-auto">
          {previewNode}
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap items-center gap-3 mt-4">
        <button
          type="button"
          onClick={handleManualSave}
          disabled={!hasChanges || status === "saving" || !reportId}
          className="px-5 py-2 bg-primary text-white text-sm font-bold rounded-xl hover:bg-teal-600 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Save
        </button>
        <button
          type="button"
          onClick={handleDiscard}
          disabled={!hasChanges}
          className="px-5 py-2 bg-slate-100 text-slate-700 text-sm font-bold rounded-xl hover:bg-slate-200 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Discard
        </button>
      </div>
    </div>
  );
}
