"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/lib/api";

interface ResponseItem {
  node_id: string | null;
  category: string;
  section: string;
  question: string;
  answer: string;
  option_label: string | null;
  is_skipped: boolean;
  is_multi: boolean;
  timestamp: string | null;
}

interface ResponseSection {
  title: string;
  items: ResponseItem[];
}

interface ResponseSession {
  session_id: string;
  flow_type: string;
  status: string;
  respondent: { name: string; email: string | null; role: string };
  started_at: string | null;
  completed_at: string | null;
  sections: ResponseSection[];
  totals: { answered: number; skipped: number };
}

interface ResponsesPayload {
  student: { id: string; first_name: string; last_name: string };
  sessions: ResponseSession[];
  viewer_role?: string | null;
}

interface QuestionnaireResponsesCardProps {
  studentId: string;
}

function relRole(role: string): { label: string; tone: string } {
  const r = (role || "").toLowerCase();
  if (/parent|mother|father|guardian|carer/.test(r)) {
    return { label: role, tone: "from-emerald-500 to-teal-500" };
  }
  if (/school|teacher|senco|tutor/.test(r)) {
    return { label: role, tone: "from-sky-500 to-indigo-500" };
  }
  return { label: role || "Guardian", tone: "from-slate-400 to-slate-600" };
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function QuestionnaireResponsesCard({
  studentId,
}: QuestionnaireResponsesCardProps) {
  const [data, setData] = useState<ResponsesPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) throw new Error("Not signed in.");
      const res = await fetch(
        `${API_BASE}/psychologist-reports/students/${studentId}/responses`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) {
        const b = await res.json().catch(() => null);
        const detail = typeof b?.detail === "string" ? b.detail : `Request failed (${res.status})`;
        throw new Error(detail);
      }
      const payload = (await res.json()) as ResponsesPayload;
      setData(payload);
      // Auto-expand the first session for convenience
      if (payload.sessions && payload.sessions.length > 0) {
        setExpandedSession(payload.sessions[0].session_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load responses.");
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    load();
  }, [load]);

  const sessions = useMemo(() => data?.sessions ?? [], [data]);

  const toggleSection = (key: string) => {
    setCollapsedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  if (loading) {
    return (
      <section className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-300 to-slate-400 animate-pulse" />
          <div className="h-5 w-48 bg-slate-200 rounded animate-pulse" />
        </div>
        <div className="space-y-2">
          <div className="h-4 bg-slate-200 rounded animate-pulse w-full" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-5/6" />
          <div className="h-4 bg-slate-200 rounded animate-pulse w-4/6" />
        </div>
      </section>
    );
  }

  return (
    <section className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl">
      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-white flex-shrink-0">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-on-background">Questionnaire Responses</h2>
            <p className="text-xs text-slate-500">
              All chatbot answers from the parent/school assessments for this student.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={load}
          className="px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm font-medium text-red-700">{error}</p>
        </div>
      )}

      {sessions.length === 0 && !error && (
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
          <p className="text-sm text-slate-600">
            No questionnaire responses yet for this student. Responses appear here as soon as a
            parent or school completes their assessment.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {sessions.map((sess) => {
          const role = relRole(sess.respondent.role);
          const open = expandedSession === sess.session_id;
          return (
            <div
              key={sess.session_id}
              className="border border-slate-200 rounded-xl overflow-hidden bg-white"
            >
              <button
                type="button"
                onClick={() =>
                  setExpandedSession((prev) =>
                    prev === sess.session_id ? null : sess.session_id
                  )
                }
                className="w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-slate-50 transition-colors text-left"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span
                    className={`text-[0.6875rem] uppercase tracking-wide font-bold text-white bg-gradient-to-r ${role.tone} px-2 py-0.5 rounded-md`}
                  >
                    {role.label}
                  </span>
                  <span className="font-semibold text-on-background truncate">
                    {sess.respondent.name}
                  </span>
                  <span className="text-[0.75rem] text-slate-500 hidden sm:inline">
                    {sess.respondent.email}
                  </span>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-xs text-slate-500">
                    {sess.totals.answered} answers
                    {sess.totals.skipped > 0 && (
                      <span className="text-amber-600"> · {sess.totals.skipped} skipped</span>
                    )}
                  </span>
                  <span className="text-xs text-slate-400">
                    {formatDate(sess.completed_at || sess.started_at)}
                  </span>
                  <span
                    className={`text-[0.6875rem] font-semibold px-2 py-0.5 rounded ${
                      sess.status === "completed"
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {sess.status === "completed" ? "Completed" : sess.status.replace(/_/g, " ")}
                  </span>
                  <svg
                    className={`w-5 h-5 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {open && (
                <div className="border-t border-slate-100 px-4 py-4 space-y-5 bg-slate-50/40">
                  {sess.sections.length === 0 ? (
                    <p className="text-sm text-slate-500 italic">
                      No paired Q&amp;A entries recorded for this session.
                    </p>
                  ) : (
                    sess.sections.map((sec, sidx) => {
                      const sectionKey = `${sess.session_id}::${sec.title}`;
                      const collapsed = !!collapsedSections[sectionKey];
                      return (
                        <div key={sidx} className="rounded-lg bg-white border border-slate-200">
                          <button
                            type="button"
                            onClick={() => toggleSection(sectionKey)}
                            className="w-full px-3 py-2 flex items-center justify-between gap-2 text-left hover:bg-slate-50"
                          >
                            <h3 className="text-sm font-bold text-on-background">
                              {sec.title}
                              <span className="ml-2 text-xs text-slate-400 font-normal">
                                ({sec.items.length} {sec.items.length === 1 ? "item" : "items"})
                              </span>
                            </h3>
                            <svg
                              className={`w-4 h-4 text-slate-400 transition-transform ${collapsed ? "" : "rotate-180"}`}
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                          {!collapsed && (
                            <div className="px-3 pb-3 pt-1 space-y-3">
                              {sec.items.map((item, idx) => (
                                <div
                                  key={`${item.node_id || idx}-${idx}`}
                                  className="text-sm"
                                >
                                  <div className="flex items-start gap-2">
                                    <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-100 text-slate-500 text-[0.6875rem] font-semibold flex-shrink-0 mt-0.5">
                                      Q
                                    </span>
                                    <p className="text-slate-800 font-medium">{item.question}</p>
                                  </div>
                                  <div className="flex items-start gap-2 mt-1.5 ml-7">
                                    {item.is_skipped ? (
                                      <span className="inline-flex items-center px-2 py-0.5 text-[0.6875rem] font-medium bg-amber-50 text-amber-700 border border-amber-200 rounded">
                                        Skipped
                                      </span>
                                    ) : (
                                      <>
                                        {item.option_label && (
                                          <span
                                            className={`inline-flex items-center px-2 py-0.5 text-[0.6875rem] font-semibold rounded ${
                                              item.is_multi
                                                ? "bg-teal-50 text-teal-700 border border-teal-200"
                                                : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                            }`}
                                          >
                                            {item.is_multi ? "Multi-select" : "Selected"}: {item.option_label}
                                          </span>
                                        )}
                                        {item.answer && item.answer !== item.option_label && (
                                          <p className="text-slate-700 whitespace-pre-wrap">
                                            {item.answer}
                                          </p>
                                        )}
                                      </>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
