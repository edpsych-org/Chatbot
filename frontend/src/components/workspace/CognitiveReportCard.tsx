"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import MarkdownEditor from "./MarkdownEditor";
import PdfUploadZone from "./PdfUploadZone";
import ScoresTable from "./ScoresTable";
import ConfirmModal from "@/components/ConfirmModal";
import { useConfirm } from "@/hooks/useConfirm";
import type { CognitiveProfile, ParsedScores, Report } from "./types";

interface CognitiveReportCardProps {
  studentId: string;
  existingReport: Report | null;
  cognitiveProfile: CognitiveProfile | null;
  onReportChange: (r: Report) => void;
  onProfileChange: (p: CognitiveProfile) => void;
}

export default function CognitiveReportCard({
  studentId,
  existingReport,
  cognitiveProfile,
  onReportChange,
  onProfileChange,
}: CognitiveReportCardProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reupload, setReupload] = useState(false);
  const [showScoresDetail, setShowScoresDetail] = useState(false);
  const { confirm, confirmProps } = useConfirm();

  const callPost = async (path: string, body?: object): Promise<Report> => {
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
  };

  const generateReport = async () => {
    const ok = await confirm(
      "This will generate a cognitive report from the uploaded scores. Continue?",
      { title: "Generate Cognitive Report", confirmLabel: "Generate" }
    );
    if (!ok) return;
    setBusy(true);
    setError(null);
    try {
      const r = await callPost(
        `/psychologist-reports/students/${studentId}/cognitive-report/generate`
      );
      onReportChange(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed.");
    } finally {
      setBusy(false);
    }
  };

  const startBlank = async () => {
    setBusy(true);
    setError(null);
    try {
      const r = await callPost(`/psychologist-reports/students/${studentId}/reports/blank`, {
        report_type: "cognitive_report",
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
        `/psychologist-reports/students/${studentId}/cognitive-report/generate`
      );
      onReportChange(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Regeneration failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleReupload = async () => {
    const ok = await confirm(
      "Re-uploading will replace the current scores. Continue?",
      { title: "Re-upload PDF", confirmLabel: "Re-upload", variant: "danger" }
    );
    if (ok) setReupload(true);
  };

  const handleScoresChange = (scores: ParsedScores) => {
    if (!cognitiveProfile) return;
    onProfileChange({ ...cognitiveProfile, parsed_scores: scores });
  };

  const header = (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-teal-500 flex items-center justify-center text-white flex-shrink-0">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-on-background">Cognitive Report</h2>
          <p className="text-xs text-slate-500">
            Upload a cognitive assessment PDF, review scores, then generate narrative.
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <section className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl">
      <ConfirmModal {...confirmProps} />
      {header}

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm font-medium text-red-700">{error}</p>
        </div>
      )}

      {/* State 1: no profile and no report */}
      {!cognitiveProfile && !existingReport && (
        <div className="space-y-4">
          <PdfUploadZone
            studentId={studentId}
            onUploaded={onProfileChange}
            disabled={busy}
          />
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-xs font-medium text-slate-400">OR</span>
            <div className="flex-1 h-px bg-slate-200" />
          </div>
          <button
            type="button"
            onClick={startBlank}
            disabled={busy}
            className="w-full sm:w-auto px-5 py-2.5 bg-slate-100 text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition-all disabled:opacity-40"
          >
            Start blank report
          </button>
        </div>
      )}

      {/* State 2: profile exists, no report yet */}
      {cognitiveProfile && !existingReport && (
        <div className="space-y-5">
          {reupload ? (
            <div>
              <PdfUploadZone
                studentId={studentId}
                onUploaded={(p) => {
                  onProfileChange(p);
                  setReupload(false);
                }}
                disabled={busy}
              />
              <button
                type="button"
                onClick={() => setReupload(false)}
                className="mt-2 text-xs text-slate-500 hover:text-slate-700 underline"
              >
                Cancel
              </button>
            </div>
          ) : (
            <>
              <ScoresTable
                scores={cognitiveProfile.parsed_scores}
                confidence={cognitiveProfile.confidence_score ?? 1}
                editable
                onScoresChange={handleScoresChange}
              />
              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={generateReport}
                  disabled={busy}
                  className="px-5 py-2.5 bg-gradient-to-r from-teal-500 to-teal-500 text-white font-bold rounded-xl shadow hover:shadow-lg transition-all disabled:opacity-40"
                >
                  {busy ? "Generating…" : "Generate Cognitive Report"}
                </button>
                <button
                  type="button"
                  onClick={handleReupload}
                  className="text-sm text-primary hover:underline"
                >
                  Re-upload PDF
                </button>
              </div>
              {busy && (
                <div className="space-y-2 pt-2">
                  <div className="h-3 bg-slate-200 rounded animate-pulse w-2/3" />
                  <div className="h-3 bg-slate-200 rounded animate-pulse w-full" />
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* State 3: report exists */}
      {existingReport && (
        <div className="space-y-5">
          {cognitiveProfile && (
            <div className="rounded-xl border border-slate-200 overflow-hidden">
              <button
                type="button"
                onClick={() => setShowScoresDetail((s) => !s)}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors"
              >
                <span className="text-sm font-semibold text-slate-700">
                  Extracted Scores
                </span>
                <svg
                  className={`w-4 h-4 text-slate-500 transition-transform ${
                    showScoresDetail ? "rotate-180" : ""
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {showScoresDetail && (
                <div className="p-4 bg-white">
                  <ScoresTable
                    scores={cognitiveProfile.parsed_scores}
                    confidence={cognitiveProfile.confidence_score ?? 1}
                  />
                </div>
              )}
            </div>
          )}
          <MarkdownEditor
            reportId={existingReport.id}
            initialContent={existingReport.content_markdown || ""}
          />
          <div className="pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={regenerate}
              disabled={!cognitiveProfile || busy}
              className="px-4 py-2 text-sm bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-slate-50 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {busy ? "Regenerating…" : "Regenerate report"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
