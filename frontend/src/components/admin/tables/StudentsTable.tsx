"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import DetailDrawer from "../DetailDrawer";
import { renderMarkdown } from "@/src/components/workspace/MarkdownEditor";
import type { AdminStudentRow } from "../types";

interface StudentsTableProps { rows: AdminStudentRow[]; }

type ReportType = "background_summary" | "cognitive_report";
type PreviewState = {
  open: boolean;
  studentName: string;
  reportType: ReportType;
  loading: boolean;
  markdown: string;
  error: string | null;
};

const EMPTY_PREVIEW: PreviewState = {
  open: false,
  studentName: "",
  reportType: "background_summary",
  loading: false,
  markdown: "",
  error: null,
};

type ScoresState = {
  open: boolean;
  studentName: string;
  loading: boolean;
  profile: any | null;
  error: string | null;
};

const EMPTY_SCORES: ScoresState = {
  open: false,
  studentName: "",
  loading: false,
  profile: null,
  error: null,
};

export default function StudentsTable({ rows }: StudentsTableProps) {
  const [preview, setPreview] = useState<PreviewState>(EMPTY_PREVIEW);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [scores, setScores] = useState<ScoresState>(EMPTY_SCORES);
  const [search, setSearch] = useState<string>("");

  if (!rows || rows.length === 0) return <EmptyState label="students" />;

  const q = search.trim().toLowerCase();
  const filteredRows = !q ? rows : rows.filter((r) => {
    const email = r.primary_guardian?.email || r.primary_guardian_email;
    const gname = r.primary_guardian?.name || r.primary_guardian_name;
    return (
      `${r.first_name} ${r.last_name}`.toLowerCase().includes(q) ||
      (r.school_name || "").toLowerCase().includes(q) ||
      (r.grade_level || "").toString().toLowerCase().includes(q) ||
      (email || "").toLowerCase().includes(q) ||
      (gname || "").toLowerCase().includes(q)
    );
  });

  const openPreview = async (row: AdminStudentRow, reportType: ReportType) => {
    const fullName = `${row.first_name} ${row.last_name}`.trim();
    setPreview({
      open: true,
      studentName: fullName,
      reportType,
      loading: true,
      markdown: "",
      error: null,
    });

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const qs = new URLSearchParams({ limit: "100", report_type: reportType });
      const res = await fetch(`${API_BASE}/admin/psychologist-reports?${qs.toString()}`, {
        headers: { Authorization: `Bearer ${token ?? ""}` },
      });
      if (!res.ok) throw new Error(`Failed to load reports (${res.status})`);
      const data = await res.json();
      const list: any[] = Array.isArray(data) ? data : data.items ?? [];
      const match = list.find((r) => r.student_id === row.id);
      if (!match) {
        setPreview((p) => ({ ...p, loading: false, error: "No report found for this student." }));
        return;
      }
      const detailRes = await fetch(`${API_BASE}/admin/psychologist-reports/${match.id}`, {
        headers: { Authorization: `Bearer ${token ?? ""}` },
      });
      if (!detailRes.ok) throw new Error(`Failed to load report (${detailRes.status})`);
      const detail = await detailRes.json();
      setPreview((p) => ({ ...p, loading: false, markdown: detail.content_markdown || "" }));
    } catch (e) {
      setPreview((p) => ({ ...p, loading: false, error: e instanceof Error ? e.message : "Error" }));
    }
  };

  const downloadWord = async (row: AdminStudentRow) => {
    setDownloadingId(row.id);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(`${API_BASE}/admin/students/${row.id}/reports/download`, {
        headers: { Authorization: `Bearer ${token ?? ""}` },
      });
      if (!res.ok) {
        let msg = `Download failed (${res.status})`;
        try {
          const b = await res.json();
          if (b?.detail) msg = b.detail;
        } catch { /* ignore */ }
        throw new Error(msg);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const safeName = `${row.first_name}${row.last_name}`.replace(/[^A-Za-z0-9]/g, "") || "Student";
      const a = document.createElement("a");
      a.href = url;
      a.download = `${safeName}_report.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Download failed");
    } finally {
      setDownloadingId(null);
    }
  };

  const closePreview = () => setPreview(EMPTY_PREVIEW);
  const closeScores = () => setScores(EMPTY_SCORES);

  const openScores = async (row: AdminStudentRow) => {
    const fullName = `${row.first_name} ${row.last_name}`.trim();
    setScores({ open: true, studentName: fullName, loading: true, profile: null, error: null });
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(`${API_BASE}/admin/cognitive-profiles`, {
        headers: { Authorization: `Bearer ${token ?? ""}` },
      });
      if (!res.ok) throw new Error(`Failed to load cognitive scores (${res.status})`);
      const list: any[] = await res.json();
      const studentProfiles = list.filter((p) => p.student_id === row.id);
      if (studentProfiles.length === 0) {
        setScores((s) => ({ ...s, loading: false, error: "No cognitive scores uploaded for this student." }));
        return;
      }
      // Prefer the most recent one (endpoint returns ordered by created_at DESC already).
      setScores((s) => ({ ...s, loading: false, profile: studentProfiles[0] }));
    } catch (e) {
      setScores((s) => ({ ...s, loading: false, error: e instanceof Error ? e.message : "Error" }));
    }
  };

  return (
    <>
      <div className="flex items-center justify-between gap-3 mb-3">
        <p className="text-[0.75rem] text-[#737373]">
          {filteredRows.length} {filteredRows.length === 1 ? "student" : "students"}
          {q ? ` · filtered from ${rows.length}` : ""}
        </p>
        <div className="relative w-full sm:w-72">
          <svg className="w-4 h-4 text-[#737373] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 103.5 10a7.5 7.5 0 0013.15 6.65z" />
          </svg>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name, school, email…"
            className="w-full h-9 pl-9 pr-3 bg-white border border-[#dedede] rounded-lg text-xs text-[#333] placeholder:text-[#a3a3a3] outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500/50 transition-all"
          />
        </div>
      </div>

      <div className="rounded-xl overflow-hidden border border-[#dedede]">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#f4f4f4] border-b border-[#dedede]">
              <tr>
                <Th>Name</Th>
                <Th>Grade</Th>
                <Th>School</Th>
                <Th>Parent/Guardian Email</Th>
                <Th>Assessment Progress</Th>
                <Th>Created</Th>
                <Th>Reports</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#eeeeee]">
              {filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-sm text-[#737373]">
                    No students match &quot;{search}&quot;.
                  </td>
                </tr>
              ) : filteredRows.map((row) => (
                <tr key={row.id} className="hover:bg-[#f4f4f4] transition-colors">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#333]">
                    {row.first_name} {row.last_name}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.grade_level || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.school_name || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {(() => {
                      const email = row.primary_guardian?.email || row.primary_guardian_email;
                      return email
                        ? <span className="text-sm text-[#333]">{email}</span>
                        : <span className="text-sm text-[#737373]">-</span>;
                    })()}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <ProgressCell status={row.assessment_status} progress={row.assessment_progress} />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">
                    {row.created_at ? new Date(row.created_at).toLocaleDateString() : "-"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-1.5 min-w-[120px]">
                      <button
                        type="button"
                        onClick={() => openPreview(row, "background_summary")}
                        className="h-7 px-2.5 text-[0.6875rem] font-medium text-[#0c888e] border border-[#dedede] rounded-md hover:bg-[#e6f7f8] hover:border-[#00acb6] transition-colors whitespace-nowrap"
                        title="Preview background report"
                      >
                        Background
                      </button>
                      <button
                        type="button"
                        onClick={() => openPreview(row, "cognitive_report")}
                        className="h-7 px-2.5 text-[0.6875rem] font-medium text-[#0c888e] border border-[#dedede] rounded-md hover:bg-[#e6f7f8] hover:border-[#00acb6] transition-colors whitespace-nowrap"
                        title="Preview cognitive report"
                      >
                        Cognitive
                      </button>
                      <button
                        type="button"
                        onClick={() => openScores(row)}
                        className="h-7 px-2.5 text-[0.6875rem] font-medium text-[#0c888e] border border-[#dedede] rounded-md hover:bg-[#e6f7f8] hover:border-[#00acb6] transition-colors whitespace-nowrap"
                        title="View cognitive scores"
                      >
                        Scores
                      </button>
                      <button
                        type="button"
                        onClick={() => downloadWord(row)}
                        disabled={downloadingId === row.id}
                        className="h-7 px-2.5 text-[0.6875rem] font-semibold text-white bg-[#00acb6] hover:bg-[#0c888e] rounded-md transition-colors disabled:opacity-50 whitespace-nowrap"
                        title="Download combined Word document"
                      >
                        {downloadingId === row.id ? "…" : "Download"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <DetailDrawer
        isOpen={preview.open}
        onClose={closePreview}
        title={
          preview.studentName
            ? `${preview.studentName} - ${preview.reportType === "background_summary" ? "Background" : "Cognitive"}`
            : "Report"
        }
      >
        <div className="flex-1 min-h-0 flex flex-col p-3 sm:p-4 lg:p-5 gap-3">
          {preview.loading && (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-4 bg-[#f4f4f4] rounded animate-pulse" />
              ))}
            </div>
          )}
          {preview.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {preview.error}
            </div>
          )}
          {!preview.loading && !preview.error && (
            <article className="max-w-none flex-1 min-h-0 overflow-y-auto text-[#333] leading-relaxed space-y-3 bg-white rounded-xl border border-[#dedede] p-6 sm:p-8 lg:p-10 [&_h1]:font-serif [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:text-[#333] [&_h1]:mt-6 [&_h1]:mb-3 [&_h2]:font-serif [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-[#333] [&_h2]:mt-5 [&_h2]:mb-2 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-[#333] [&_h3]:mt-4 [&_h3]:mb-2 [&_p]:text-[0.9375rem] [&_p]:text-[#333] [&_ul]:pl-5 [&_ul]:list-disc [&_ul]:text-[0.9375rem] [&_ul]:text-[#333] [&_li]:mt-1">
              {renderMarkdown(preview.markdown || "")}
            </article>
          )}
        </div>
      </DetailDrawer>

      <DetailDrawer
        isOpen={scores.open}
        onClose={closeScores}
        title={scores.studentName ? `${scores.studentName} — Cognitive Scores` : "Cognitive Scores"}
      >
        <div className="flex-1 min-h-0 flex flex-col p-3 sm:p-4 lg:p-5 gap-3">
          {scores.loading && (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-4 bg-[#f4f4f4] rounded animate-pulse" />
              ))}
            </div>
          )}
          {scores.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {scores.error}
            </div>
          )}
          {!scores.loading && !scores.error && scores.profile && (
            <CognitiveScoresCard profile={scores.profile} />
          )}
        </div>
      </DetailDrawer>
    </>
  );
}

function CognitiveScoresCard({ profile }: { profile: any }) {
  const parsed = profile.parsed_scores || {};
  const entries = Object.entries(parsed).filter(([, v]) => v !== null && v !== undefined && v !== "");

  return (
    <article className="max-w-none flex-1 min-h-0 overflow-y-auto bg-white rounded-xl border border-[#dedede] p-6 sm:p-8 lg:p-10 space-y-6">
      {/* Header meta */}
      <header className="pb-4 border-b border-[#eeeeee]">
        <h3 className="text-xl font-semibold text-[#333]">
          {profile.test_name || "Cognitive test"}
        </h3>
        <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-3 text-[0.8125rem]">
          <div>
            <div className="text-[0.6875rem] uppercase tracking-wider text-[#737373]">Test date</div>
            <div className="font-medium text-[#333]">
              {profile.test_date ? new Date(profile.test_date).toLocaleDateString() : "—"}
            </div>
          </div>
          <div>
            <div className="text-[0.6875rem] uppercase tracking-wider text-[#737373]">Confidence</div>
            <div className="font-medium text-[#333]">
              {profile.confidence_score != null ? `${Math.round(profile.confidence_score * 100)}%` : "—"}
            </div>
          </div>
          <div>
            <div className="text-[0.6875rem] uppercase tracking-wider text-[#737373]">Requires review</div>
            <div className="font-medium">
              {profile.requires_review ? (
                <span className="text-amber-700">Yes</span>
              ) : (
                <span className="text-emerald-700">No</span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Scores */}
      {entries.length === 0 ? (
        <p className="text-sm text-[#737373] italic">No parsed scores available for this profile.</p>
      ) : (
        <div>
          <h4 className="text-[0.75rem] font-semibold uppercase tracking-wider text-[#737373] mb-3">
            Parsed scores
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {entries.map(([key, value]) => (
              <div
                key={key}
                className="p-3 bg-[#f9f9f9] border border-[#eeeeee] rounded-lg"
              >
                <div className="text-[0.6875rem] uppercase tracking-wider text-[#737373]">
                  {formatKey(key)}
                </div>
                <div className="text-lg font-semibold text-[#333]">
                  {String(value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

function formatKey(k: string): string {
  // Acronyms stay uppercase (FSIQ, VCI, WMI, PSI, etc.); otherwise title-case underscores.
  if (/^[A-Z0-9_]+$/.test(k)) return k.replace(/_/g, " ");
  return k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">{children}</th>;
}

interface Progress { done?: number | null; total?: number | null; percent?: number | null }

function ProgressCell({ status, progress }: { status?: string | null; progress?: Progress | null }) {
  const s = (status || "NOT_ASSIGNED").toUpperCase();
  const pct = Math.max(0, Math.min(100, progress?.percent ?? 0));
  const done = progress?.done ?? 0;
  const total = progress?.total ?? 0;

  const labels: Record<string, string> = {
    COMPLETED: "Completed",
    IN_PROGRESS: "In progress",
    ASSIGNED: "Assigned",
    CANCELLED: "Cancelled",
    NOT_ASSIGNED: "Not assigned",
  };
  const label = labels[s] || labels.NOT_ASSIGNED;

  // Bar colour: green when 100%, amber when partial, slate when nothing to show.
  let barCls = "bg-slate-300";
  if (pct >= 100) barCls = "bg-emerald-500";
  else if (pct > 0) barCls = "bg-amber-400";
  const trackCls = s === "CANCELLED" ? "bg-slate-200 opacity-50" : "bg-slate-200";

  return (
    <div className="min-w-[160px] max-w-[220px]">
      <div className={`h-1.5 rounded-full overflow-hidden ${trackCls}`}>
        <div
          className={`h-full ${barCls} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex items-center justify-between mt-1">
        <span className={`text-[0.6875rem] font-medium ${s === "CANCELLED" ? "text-slate-400 line-through" : "text-[#737373]"}`}>
          {label}
        </span>
        <span className="text-[0.6875rem] font-semibold text-[#333]">
          {total > 0 ? `${done}/${total}` : `${pct}%`}
        </span>
      </div>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="py-12 text-center">
      <p className="text-sm text-[#737373]">No {label} found</p>
    </div>
  );
}
