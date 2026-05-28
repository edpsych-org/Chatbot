"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import MarkdownEditor from "./MarkdownEditor";
import ConfirmModal from "@/components/ConfirmModal";
import { useConfirm } from "@/hooks/useConfirm";
import type { Report } from "./types";

export type BackgroundVoice = "parent" | "school" | "combined";

interface BackgroundSummaryCardProps {
  studentId: string;
  existingReport: Report | null;
  /** Which voice this card renders. Defaults to "combined" (legacy behaviour). */
  voice?: BackgroundVoice;
  /** Whether at least one assessor of this voice has completed. */
  voiceReady?: boolean;
  /** Names of pending assessors of this voice (shown in the waiting hint). */
  pendingForVoice?: string[];
  /** Whether this voice has any assigned assessors at all. */
  voiceAssigned?: boolean;
  /** Legacy combined-mode props (kept for backward compat). */
  hasParentData?: boolean;
  allAssessorsComplete?: boolean;
  pendingRoles?: string[];
  completionCount?: { done: number; total: number };
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
    const errBody = await res.json().catch(() => null);
    let detail = `Request failed (${res.status})`;
    if (typeof errBody?.detail === "string") detail = errBody.detail;
    else if (errBody?.detail && typeof errBody.detail === "object" && typeof errBody.detail.message === "string") detail = errBody.detail.message;
    throw new Error(detail);
  }
  return (await res.json()) as Report;
}

interface VoiceConfig {
  title: string;
  subtitle: string;
  generateButtonLabel: string;
  regenerateButtonLabel: string;
  apiPath: string;
  reportType: "background_summary" | "background_summary_parent" | "background_summary_school";
  accentFrom: string;
  accentTo: string;
  iconPath: string;
}

const VOICE_CONFIG: Record<BackgroundVoice, VoiceConfig> = {
  parent: {
    title: "Parent Background Summary",
    subtitle: "Narrative drawn ONLY from the parent's completed responses. Grounded — every claim maps to a stated answer.",
    generateButtonLabel: "Generate from parent data",
    regenerateButtonLabel: "Regenerate from parent data",
    apiPath: "/background-summary-parent/generate",
    reportType: "background_summary_parent",
    accentFrom: "from-emerald-500",
    accentTo: "to-teal-500",
    iconPath:
      "M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-5.13a4 4 0 11-8 0 4 4 0 018 0zm6 3a3 3 0 11-6 0 3 3 0 016 0z",
  },
  school: {
    title: "School Background Summary",
    subtitle: "Narrative drawn ONLY from the school's completed responses. Grounded — every claim maps to a stated answer.",
    generateButtonLabel: "Generate from school data",
    regenerateButtonLabel: "Regenerate from school data",
    apiPath: "/background-summary-school/generate",
    reportType: "background_summary_school",
    accentFrom: "from-sky-500",
    accentTo: "to-indigo-500",
    iconPath:
      "M12 14l9-5-9-5-9 5 9 5zm0 0v6m-7-3l7 4 7-4",
  },
  combined: {
    title: "Background Summary",
    subtitle: "Narrative drawn from parent responses (attention, social, emotional, academic).",
    generateButtonLabel: "Generate from parent data",
    regenerateButtonLabel: "Regenerate from parent data",
    apiPath: "/background-summary/generate",
    reportType: "background_summary",
    accentFrom: "from-emerald-500",
    accentTo: "to-teal-500",
    iconPath:
      "M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-5.13a4 4 0 11-8 0 4 4 0 018 0zm6 3a3 3 0 11-6 0 3 3 0 016 0z",
  },
};

export default function BackgroundSummaryCard({
  studentId,
  existingReport,
  voice = "combined",
  voiceReady,
  pendingForVoice,
  voiceAssigned,
  hasParentData,
  allAssessorsComplete,
  pendingRoles,
  completionCount,
  onReportChange,
}: BackgroundSummaryCardProps) {
  const cfg = VOICE_CONFIG[voice];

  // Voice-scoped cards use voiceReady/pendingForVoice; combined card keeps
  // the legacy hasParentData/allAssessorsComplete gate.
  const gateReady = voice === "combined"
    ? (allAssessorsComplete ?? hasParentData ?? false)
    : (voiceReady ?? false);
  const isAssigned = voice === "combined" ? true : (voiceAssigned ?? false);

  const waitingHint = voice === "combined"
    ? (pendingRoles && pendingRoles.length > 0
      ? `Waiting for: ${pendingRoles.join(", ")}`
      : "Waiting for the parent assessment to complete.")
    : (pendingForVoice && pendingForVoice.length > 0
      ? `Waiting for: ${pendingForVoice.join(", ")}`
      : isAssigned
        ? `Waiting for the ${voice} assessment to complete.`
        : `No ${voice} assessor has been assigned yet.`);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { confirm, confirmProps } = useConfirm();

  const doGenerate = async () => {
    const ok = await confirm(
      `This will generate the ${voice === "combined" ? "" : voice + " "}background summary from the ${voice === "school" ? "school" : "parent"} questionnaire data. Continue?`,
      { title: `Generate ${cfg.title}`, confirmLabel: "Generate" }
    );
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      const report = await callEndpoint(
        `/psychologist-reports/students/${studentId}${cfg.apiPath}`
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
        { report_type: cfg.reportType }
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
        `/psychologist-reports/students/${studentId}${cfg.apiPath}`
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
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${cfg.accentFrom} ${cfg.accentTo} flex items-center justify-center text-white flex-shrink-0`}>
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={cfg.iconPath}
              />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-on-background">{cfg.title}</h2>
            <p className="text-xs text-slate-500">{cfg.subtitle}</p>
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
              disabled={!gateReady || busy}
              title={!gateReady ? waitingHint : undefined}
              aria-disabled={!gateReady || busy}
              className={`px-5 py-2.5 bg-gradient-to-r ${cfg.accentFrom} ${cfg.accentTo} text-white font-bold rounded-xl shadow hover:shadow-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              {cfg.generateButtonLabel}
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
          {!gateReady && (
            <p className="text-[0.75rem] text-amber-600 mt-2">
              {waitingHint}
            </p>
          )}
          {voice === "combined" && gateReady && completionCount && completionCount.total > 1 && (
            <p className="text-[0.75rem] text-emerald-600 mt-2">
              All {completionCount.total} assessors complete.
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
              disabled={!gateReady || busy}
              title={!gateReady ? waitingHint : undefined}
              aria-disabled={!gateReady || busy}
              className="px-4 py-2 text-sm bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy ? "Regenerating…" : cfg.regenerateButtonLabel}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
