"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import MarkdownEditor from "./MarkdownEditor";
import ConfirmModal from "@/components/ConfirmModal";
import { useConfirm } from "@/hooks/useConfirm";
import type { Report } from "./types";

interface BackgroundSummaryCardProps {
  studentId: string;
  existingReport: Report | null;
  hasParentData: boolean;
  onReportChange: (r: Report) => void;
}

async function callEndpoint(path: string, body?: object): Promise<Report> {
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

export default function BackgroundSummaryCard({
  studentId,
  existingReport,
  hasParentData,
  onReportChange,
}: BackgroundSummaryCardProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { confirm, confirmProps } = useConfirm();

  const doGenerate = async () => {
    const ok = await confirm(
      "This will generate a background summary from the parent assessment data. Continue?",
      { title: "Generate Background Summary", confirmLabel: "Generate" }
    );
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      const report = await callEndpoint(
        `/psychologist-reports/students/${studentId}/background-summary/generate`
      );
      onReportChange(report);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed.");
    } finally {
      setBusy(false);
    }
  };

  const doBlank = async () => {
    setBusy(true);
    setError(null);
    try {
      const report = await callEndpoint(
        `/psychologist-reports/students/${studentId}/reports/blank`,
        { report_type: "background_summary" }
      );
      onReportChange(report);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create blank report.");
    } finally {
      setBusy(false);
    }
  };

  const doRegenerate = async () => {
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
      const report = await callEndpoint(
        `/psychologist-reports/students/${studentId}/background-summary/generate`
      );
      onReportChange(report);
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
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white flex-shrink-0">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-5.13a4 4 0 11-8 0 4 4 0 018 0zm6 3a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-on-background">Background Summary</h2>
            <p className="text-xs text-slate-500" title="Generated from the parent's completed assessment.">
              Narrative drawn from parent responses (attention, social, emotional, academic).
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm font-medium text-red-700">{error}</p>
        </div>
      )}

      {busy && !existingReport ? (
        <div className="space-y-3">
          <div className="h-4 bg-slate-200 rounded animate-pulse w-1/3" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-full" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-5/6" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-4/6" />
          <p className="text-xs text-slate-500 mt-2">
            Generating report — this may take up to 90 seconds.
          </p>
        </div>
      ) : !existingReport ? (
        <div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={doGenerate}
              disabled={!hasParentData || busy}
              className="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold rounded-xl shadow hover:shadow-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Generate from parent data
            </button>
            <button
              type="button"
              onClick={doBlank}
              disabled={busy}
              className="px-5 py-2.5 bg-slate-100 text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition-all disabled:opacity-40"
            >
              Start blank
            </button>
          </div>
          {!hasParentData && (
            <p className="mt-3 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 inline-block">
              Parent hasn't completed the assessment yet — you can still start blank.
            </p>
          )}
        </div>
      ) : (
        <div>
          <MarkdownEditor
            reportId={existingReport.id}
            initialContent={existingReport.content_markdown || ""}
          />
          <div className="mt-4 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={doRegenerate}
              disabled={!hasParentData || busy}
              className="px-4 py-2 text-sm bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy ? "Regenerating…" : "Regenerate from parent data"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
