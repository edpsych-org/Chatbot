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

  const backgroundReport = useMemo(
    () => workspace?.reports?.background_summary?.[0] ?? null,
    [workspace]
  );
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

  const hasParentData = Boolean(workspace?.latest_completed_session);

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
      <header className="bg-white/90 backdrop-blur border-b border-slate-200 sticky top-0 z-40">
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
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
        <div className="space-y-6 sm:space-y-8">
          <BackgroundSummaryCard
            studentId={studentId}
            existingReport={backgroundReport}
            hasParentData={hasParentData}
            onReportChange={upsertReport}
          />

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
