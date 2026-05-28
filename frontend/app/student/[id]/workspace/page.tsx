"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";
import BackgroundSummaryCard from "@/src/components/workspace/BackgroundSummaryCard";
import CognitiveReportCard from "@/src/components/workspace/CognitiveReportCard";
import UnifiedInsightsCard from "@/src/components/workspace/UnifiedInsightsCard";
import type {
  CognitiveProfile,
  Report,
  WorkspaceResponse,
  GroupedReports,
} from "@/src/components/workspace/types";

export default function ReportsWorkspacePage() {
  const router = useRouter();
  const params = useParams();
  const studentId = params.id as string;

  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const loadWorkspace = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const wsRes = await fetch(
        `${API_BASE}/psychologist-reports/students/${studentId}/workspace`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (wsRes.status === 401) {
        localStorage.removeItem("access_token");
        router.push("/login");
        return;
      }
      if (!wsRes.ok) {
        let detail = `Failed to load workspace (${wsRes.status})`;
        try {
          const b = await wsRes.json();
          if (b?.detail) detail = b.detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }

      const ws = (await wsRes.json()) as WorkspaceResponse;
      setWorkspace(ws);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load workspace.");
    } finally {
      setLoading(false);
    }
  }, [studentId, router]);

  useEffect(() => {
    loadWorkspace();
  }, [loadWorkspace]);

  const parentBackgroundReport = useMemo(
    () => workspace?.reports?.background_summary_parent?.[0] ?? null,
    [workspace]
  );
  const schoolBackgroundReport = useMemo(
    () => workspace?.reports?.background_summary_school?.[0] ?? null,
    [workspace]
  );
  const legacyBackgroundReport = useMemo(
    () => workspace?.reports?.background_summary?.[0] ?? null,
    [workspace]
  );
  // For Unified Insights gating + .docx download eligibility, treat any of
  // the three background variants as a valid background report.
  const backgroundReport = parentBackgroundReport || schoolBackgroundReport || legacyBackgroundReport;
  const cognitiveReport = useMemo(
    () => workspace?.reports?.cognitive_report?.[0] ?? null,
    [workspace]
  );
  const unifiedReport = useMemo(
    () => workspace?.reports?.unified_insights?.[0] ?? null,
    [workspace]
  );
  const cognitiveProfile: CognitiveProfile | null = useMemo(
    () => (workspace?.cognitive_profiles && workspace.cognitive_profiles[0]) || null,
    [workspace]
  );

  const assessors = workspace?.assessors ?? [];
  const completionCount = workspace?.completion_count ?? { done: 0, total: 0 };

  // Voice-scoped readiness — parent and school cards advance independently.
  const isParentRole = (r: string) => {
    const t = (r || "").toLowerCase();
    return /parent|mother|father|guardian|carer|caregiver|step.?(mother|father)/.test(t);
  };
  const isSchoolRole = (r: string) => {
    const t = (r || "").toLowerCase();
    return /school|teacher|senco|sendco|tutor|head of (year|learning)/.test(t);
  };

  const parentAssessors = assessors.filter((a) => isParentRole(a.relationship_type));
  const schoolAssessors = assessors.filter((a) => isSchoolRole(a.relationship_type));

  const parentVoiceAssigned = parentAssessors.length > 0;
  const schoolVoiceAssigned = schoolAssessors.length > 0;
  const parentVoiceReady = parentAssessors.some((a) => a.status === "COMPLETED");
  const schoolVoiceReady = schoolAssessors.some((a) => a.status === "COMPLETED");
  const pendingForParent = parentAssessors
    .filter((a) => a.status !== "COMPLETED" && a.status !== "CANCELLED")
    .map((a) => a.guardian_name || a.relationship_type || "Parent");
  const pendingForSchool = schoolAssessors
    .filter((a) => a.status !== "COMPLETED" && a.status !== "CANCELLED")
    .map((a) => a.guardian_name || a.relationship_type || "School");

  const upsertReport = (incoming: Report) => {
    setWorkspace((prev) => {
      if (!prev) return prev;
      const key = incoming.report_type as keyof GroupedReports;
      return {
        ...prev,
        reports: {
          ...prev.reports,
          [key]: [incoming],
        },
      };
    });
  };

  const hasAnyReport = Boolean(backgroundReport || cognitiveReport || unifiedReport);

  const goHome = () => {
    try {
      const raw = localStorage.getItem("user");
      const role = (raw ? JSON.parse(raw)?.role : "") || "";
      const upper = String(role).toUpperCase();
      if (upper === "ADMIN") router.push("/admin/dashboard");
      else if (upper === "PSYCHOLOGIST") router.push("/psychologist/dashboard");
      else router.push("/dashboard");
    } catch {
      router.push("/dashboard");
    }
  };

  const downloadDocx = async () => {
    setDownloading(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) { router.push("/login"); return; }
      const res = await fetch(
        `${API_BASE}/psychologist-reports/students/${studentId}/report.docx`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
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
      const safe = (workspace?.student
        ? `${workspace.student.first_name}${workspace.student.last_name}`
        : "Student"
      ).replace(/[^A-Za-z0-9]/g, "") || "Student";
      const a = document.createElement("a");
      a.href = url;
      a.download = `${safe}_report.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  const upsertProfile = (incoming: CognitiveProfile) => {
    setWorkspace((prev) => {
      if (!prev) return prev;
      const others = prev.cognitive_profiles.filter((p) => p.id !== incoming.id);
      return { ...prev, cognitive_profiles: [incoming, ...others] };
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500 font-medium">Loading workspace…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <svg
            className="w-16 h-16 text-red-400 mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          <h2 className="text-xl font-bold text-on-background mb-2">Something went wrong</h2>
          <p className="text-slate-500 mb-6">{error}</p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={loadWorkspace}
              className="px-5 py-2.5 bg-primary text-white font-bold rounded-xl hover:bg-teal-600 transition-all"
            >
              Retry
            </button>
            <button
              onClick={() => router.push(`/student/${studentId}`)}
              className="px-5 py-2.5 bg-slate-100 text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition-all"
            >
              Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  const studentName = workspace?.student
    ? `${workspace.student.first_name} ${workspace.student.last_name}`
    : "Student";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-teal-50/30 to-emerald-50/30">
      {/* Sticky header */}
      <header className="site-header-pinned bg-white/90 backdrop-blur border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 min-w-0">
              <button
                onClick={() => router.push(`/student/${studentId}`)}
                className="w-10 h-10 rounded-xl bg-surface hover:bg-slate-200 transition-colors flex items-center justify-center flex-shrink-0"
                aria-label="Back to student"
              >
                <svg
                  className="w-5 h-5 text-slate-600"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-primary uppercase tracking-wide">
                  Reports Workspace
                </p>
                <h1 className="text-lg sm:text-xl font-black text-on-background truncate">
                  {studentName}
                </h1>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={goHome}
                title="Go to dashboard"
                className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl bg-slate-100 text-slate-700 text-xs sm:text-sm font-semibold hover:bg-slate-200 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l9-9 9 9M5 10v10a1 1 0 001 1h3v-6h6v6h3a1 1 0 001-1V10" />
                </svg>
                <span className="hidden sm:inline">Dashboard</span>
              </button>
              <button
                onClick={downloadDocx}
                disabled={!hasAnyReport || downloading}
                title={hasAnyReport ? "Download combined Word document" : "Generate at least one report first"}
                className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl bg-primary text-white text-xs sm:text-sm font-semibold hover:bg-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
                </svg>
                <span className="hidden sm:inline">{downloading ? "Preparing…" : "Download .docx"}</span>
                <span className="sm:hidden">{downloading ? "…" : "Download"}</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
        <div className="space-y-6 sm:space-y-8">
          <section className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h2 className="text-lg font-bold text-on-background">Assessment Progress</h2>
                <p className="text-xs text-slate-500 mt-1">
                  {completionCount.total > 0
                    ? `${completionCount.done} of ${completionCount.total} complete`
                    : "No assessments assigned yet"}
                </p>
              </div>
            </div>
            {assessors.length === 0 ? (
              <p className="text-sm text-slate-400 italic">No assessments assigned yet</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {assessors.map((a) => {
                  const statusStyles =
                    a.status === "COMPLETED"
                      ? "bg-emerald-100 text-emerald-700"
                      : a.status === "IN_PROGRESS"
                      ? "bg-amber-100 text-amber-700"
                      : a.status === "CANCELLED"
                      ? "bg-slate-100 text-slate-400 line-through"
                      : "bg-slate-100 text-slate-600";
                  return (
                    <li key={a.assignment_id} className="flex items-center gap-3 py-2.5">
                      <span className="text-sm font-medium text-slate-700 flex-1 min-w-0 truncate">
                        {a.guardian_name}
                      </span>
                      <span className="px-2 py-0.5 rounded-md text-[0.6875rem] font-medium bg-slate-50 border border-slate-200 text-slate-600">
                        {a.relationship_type || "Guardian"}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[0.6875rem] font-semibold ${statusStyles}`}>
                        {a.status}
                      </span>
                      <span className="text-[0.6875rem] text-slate-400 w-32 text-right">
                        {a.completed_at ? new Date(a.completed_at).toLocaleString() : "—"}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          {parentVoiceAssigned && (
            <BackgroundSummaryCard
              studentId={studentId}
              existingReport={parentBackgroundReport}
              voice="parent"
              voiceReady={parentVoiceReady}
              voiceAssigned={parentVoiceAssigned}
              pendingForVoice={pendingForParent}
              onReportChange={upsertReport}
            />
          )}

          {schoolVoiceAssigned && (
            <BackgroundSummaryCard
              studentId={studentId}
              existingReport={schoolBackgroundReport}
              voice="school"
              voiceReady={schoolVoiceReady}
              voiceAssigned={schoolVoiceAssigned}
              pendingForVoice={pendingForSchool}
              onReportChange={upsertReport}
            />
          )}

          {!parentVoiceAssigned && !schoolVoiceAssigned && (
            <section className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl">
              <h2 className="text-xl font-bold text-on-background mb-2">
                Background Summary
              </h2>
              <p className="text-sm text-amber-600">
                No assessors are assigned to this student yet. Assign at least one
                parent or school assessor to enable background summary generation.
              </p>
            </section>
          )}

          <CognitiveReportCard
            studentId={studentId}
            existingReport={cognitiveReport}
            cognitiveProfile={cognitiveProfile}
            onReportChange={upsertReport}
            onProfileChange={upsertProfile}
          />

          <UnifiedInsightsCard
            studentId={studentId}
            existingReport={unifiedReport}
            hasBackgroundSummary={Boolean(backgroundReport)}
            hasCognitiveReport={Boolean(cognitiveReport)}
            onReportChange={upsertReport}
          />
        </div>
      </main>
    </div>
  );
}
