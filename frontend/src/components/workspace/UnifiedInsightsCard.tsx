"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import MarkdownEditor from "./MarkdownEditor";
import ConfirmModal from "@/components/ConfirmModal";
import { useConfirm } from "@/hooks/useConfirm";
import type { Report } from "./types";

interface UnifiedInsightsCardProps {
  studentId: string;
  existingReport: Report | null;
  hasBackgroundSummary: boolean;
  hasCognitiveReport: boolean;
  onReportChange: (r: Report) => void;
}

async function callPost(path: string, body?: object): Promise<Report> {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("Not signed in.");
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const b = await res.json();
      if (b?.detail) detail = b.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await res.json()) as Report;
}

export default function UnifiedInsightsCard({
  studentId,
  existingReport,
  hasBackgroundSummary,
  hasCognitiveReport,
  onReportChange,
}: UnifiedInsightsCardProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { confirm, confirmProps } = useConfirm();

  const canSynthesize = hasBackgroundSummary && hasCognitiveReport;

  const synthesize = async () => {
    const ok = await confirm(
      "This will generate unified insights from the background summary and cognitive report. Continue?",
      { title: "Generate Unified Insights", confirmLabel: "Generate" }
    );
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      const r = await callPost(
        `/psychologist-reports/students/${studentId}/unified-insights/generate`
      );
      onReportChange(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Synthesis failed.");
    } finally {
      setBusy(false);
    }
  };

  const startBlank = async () => {
    setBusy(true);
    setError(null);
    try {
      const r = await callPost(`/psychologist-reports/students/${studentId}/reports/blank`, {
        report_type: "unified_insights",
      });
      onReportChange(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create blank report.");
    } finally {
      setBusy(false);
    }
  };

  const regenerate = async () => {
    const ok = await confirm(
      "Regenerating will replace the current draft and your edits will be lost. Continue?",
      { title: "Regenerate Report", confirmLabel: "Regenerate", variant: "danger" }
    );
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      if (existingReport) {
        const token = localStorage.getItem("access_token");
        await fetch(`${API_BASE}/psychologist-reports/reports/${existingReport.id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      const r = await callPost(
        `/psychologist-reports/students/${studentId}/unified-insights/generate`
      );
      onReportChange(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Regeneration failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl">
      <ConfirmModal {...confirmProps} />

      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-pink-500 flex items-center justify-center text-white flex-shrink-0">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-on-background">Unified Insights</h2>
            <p className="text-xs text-slate-500">
              Cross-references the background summary and cognitive report — convergence & divergence.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm font-medium text-red-700">{error}</p>
        </div>
      )}

      {!canSynthesize && !existingReport && (
        <div className="p-5 rounded-xl bg-slate-50 border border-dashed border-slate-300 text-center">
          <p className="text-sm font-medium text-slate-600">
            Both <strong>Background Summary</strong> and <strong>Cognitive Report</strong> are needed
            before synthesizing insights.
          </p>
          <div className="mt-3 flex flex-wrap items-center justify-center gap-2 text-xs">
            <span
              className={`px-2 py-1 rounded-full font-semibold ${
                hasBackgroundSummary
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-slate-200 text-slate-500"
              }`}
            >
              {hasBackgroundSummary ? "✓" : "○"} Background Summary
            </span>
            <span
              className={`px-2 py-1 rounded-full font-semibold ${
                hasCognitiveReport
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-slate-200 text-slate-500"
              }`}
            >
              {hasCognitiveReport ? "✓" : "○"} Cognitive Report
            </span>
          </div>
        </div>
      )}

      {canSynthesize && !existingReport && !busy && (
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={synthesize}
            disabled={busy}
            className="px-5 py-2.5 bg-gradient-to-r from-teal-500 to-pink-500 text-white font-bold rounded-xl shadow hover:shadow-lg transition-all disabled:opacity-40"
          >
            Synthesize Insights
          </button>
          <button
            type="button"
            onClick={startBlank}
            disabled={busy}
            className="px-5 py-2.5 bg-slate-100 text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition-all disabled:opacity-40"
          >
            Start blank
          </button>
        </div>
      )}

      {busy && !existingReport && (
        <div className="space-y-3">
          <div className="h-4 bg-slate-200 rounded animate-pulse w-1/3" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-full" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-5/6" />
          <p className="text-xs text-slate-500 mt-2">
            Synthesizing insights across both reports — this usually takes 10–20 seconds.
          </p>
        </div>
      )}

      {existingReport && (
        <div>
          <MarkdownEditor
            reportId={existingReport.id}
            initialContent={existingReport.content_markdown || ""}
          />
          <div className="mt-4 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={regenerate}
              disabled={!canSynthesize || busy}
              className="px-4 py-2 text-sm bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy ? "Regenerating…" : "Regenerate"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
