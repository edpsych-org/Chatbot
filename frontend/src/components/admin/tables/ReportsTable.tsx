"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";
import DetailDrawer from "../DetailDrawer";
import { renderMarkdown } from "@/src/components/workspace/MarkdownEditor";
import type { AdminReportRow, ReportType } from "../types";

type ReportFilter = "all" | ReportType;
interface ReportsTableProps { initialRows: AdminReportRow[]; }

export default function ReportsTable({ initialRows }: ReportsTableProps) {
  const [rows, setRows] = useState<AdminReportRow[]>(initialRows);
  const [filter, setFilter] = useState<ReportFilter>("all");
  const [filterLoading, setFilterLoading] = useState(false);
  const [selected, setSelected] = useState<AdminReportRow | null>(null);
  const [detail, setDetail] = useState<AdminReportRow | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editDraft, setEditDraft] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => { setRows(initialRows); }, [initialRows]);

  const applyFilter = async (next: ReportFilter) => {
    setFilter(next); setFilterLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const qs = new URLSearchParams({ limit: "100" });
      if (next !== "all") qs.set("report_type", next);
      const res = await fetch(`${API_BASE}/admin/psychologist-reports?${qs.toString()}`, { headers: { Authorization: `Bearer ${token ?? ""}` } });
      if (res.ok) { const data = await res.json(); setRows(Array.isArray(data) ? data : data.items ?? []); }
    } catch {} finally { setFilterLoading(false); }
  };

  const openRow = async (row: AdminReportRow) => {
    setSelected(row); setDetail(null); setDetailError(null); setDetailLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(`${API_BASE}/admin/psychologist-reports/${row.id}`, { headers: { Authorization: `Bearer ${token ?? ""}` } });
      if (res.ok) setDetail(await res.json()); else setDetailError(`Failed to load report (${res.status})`);
    } catch { setDetailError("Network error loading report"); } finally { setDetailLoading(false); }
  };

  const close = () => {
    setSelected(null); setDetail(null); setDetailError(null);
    setEditing(false); setEditDraft(""); setSaveError(null);
  };

  const startEdit = () => {
    if (!detail) return;
    setEditDraft(detail.content_markdown || "");
    setEditing(true);
    setSaveError(null);
  };

  const cancelEdit = () => {
    setEditing(false);
    setEditDraft("");
    setSaveError(null);
  };

  const saveEdit = async () => {
    if (!detail) return;
    setSavingEdit(true); setSaveError(null);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(`${API_BASE}/psychologist-reports/reports/${detail.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token ?? ""}` },
        body: JSON.stringify({ content_markdown: editDraft }),
      });
      if (!res.ok) {
        const b = await res.json().catch(() => null);
        throw new Error(b?.detail || `Save failed (${res.status})`);
      }
      const updated = await res.json();
      setDetail({ ...detail, content_markdown: updated.content_markdown, updated_at: updated.updated_at });
      setRows((prev) => prev.map((r) =>
        r.id === detail.id
          ? { ...r, updated_at: updated.updated_at, content_preview: (updated.content_markdown || "").slice(0, 160) }
          : r
      ));
      setEditing(false);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSavingEdit(false);
    }
  };

  return (
    <>
      <div className="flex flex-wrap gap-1.5 mb-4">
        {(["all", "background_summary", "cognitive_report", "unified_insights"] as ReportFilter[]).map((f) => (
          <button key={f} onClick={() => applyFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filter === f ? "bg-[#00acb6] text-[#333]" : "bg-[#f4f4f4] text-[#737373] hover:bg-[#eeeeee]"}`}>
            {f === "all" ? "All" : f === "background_summary" ? "Background" : f === "cognitive_report" ? "Cognitive" : "Unified"}
          </button>
        ))}
      </div>

      {filterLoading ? (
        <div className="space-y-2">{[1,2,3,4].map(i => <div key={i} className="h-12 bg-[#f4f4f4] rounded-lg animate-pulse" />)}</div>
      ) : rows.length === 0 ? (
        <div className="py-12 text-center"><p className="text-sm text-[#737373]">No reports found</p></div>
      ) : (
        <div className="rounded-xl overflow-hidden border border-[#dedede]">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#f4f4f4] border-b border-[#dedede]">
                <tr><Th>Student</Th><Th>Type</Th><Th>Status</Th><Th>Created</Th><Th>Updated</Th><Th>Preview</Th></tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {rows.map((row) => (
                  <tr key={row.id} onClick={() => openRow(row)} className="hover:bg-[#f4f4f4] transition-colors cursor-pointer">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#333]">{row.student_name || "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap"><TypeBadge type={row.report_type} /></td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.status}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{new Date(row.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.updated_at ? new Date(row.updated_at).toLocaleDateString() : "-"}</td>
                    <td className="px-4 py-3 text-sm text-[#737373] max-w-xs truncate">{(row.content_preview || "").slice(0, 100)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <DetailDrawer isOpen={selected !== null} onClose={close} title={selected ? `${selected.student_name || "Report"} - ${formatType(selected.report_type)}` : "Report"}>
        {detailLoading && <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-4 bg-[#f4f4f4] rounded animate-pulse" />)}</div>}
        {detailError && <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400 mb-4">{detailError}</div>}
        {!detailLoading && detail && (
          <div className="flex-1 min-h-0 flex flex-col p-3 sm:p-4 lg:p-5 gap-3">
            {/* Toolbar — sticky at top so the Edit button is always visible */}
            <div className="flex items-center justify-end gap-2 shrink-0">
              {editing ? (
                <>
                  <span className="text-[0.75rem] text-[#737373] mr-auto">Editing — changes save to the generated report.</span>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    disabled={savingEdit}
                    className="h-8 px-3 text-[0.8125rem] font-medium text-[#737373] border border-[#dedede] rounded-lg hover:bg-[#f4f4f4] disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={saveEdit}
                    disabled={savingEdit}
                    className="h-8 px-3 text-[0.8125rem] font-semibold text-white bg-[#00acb6] hover:bg-[#0c888e] rounded-lg disabled:opacity-50"
                  >
                    {savingEdit ? "Saving…" : "Save changes"}
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={startEdit}
                  className="h-8 px-3 text-[0.8125rem] font-semibold text-[#00acb6] border border-[#00acb6] rounded-lg hover:bg-[#e6f7f8]"
                >
                  Edit report
                </button>
              )}
            </div>

            {saveError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600 shrink-0">
                {saveError}
              </div>
            )}

            {/* Content box — fills 85vh, scrolls internally if content overflows */}
            {editing ? (
              <textarea
                value={editDraft}
                onChange={(e) => setEditDraft(e.target.value)}
                className="w-full flex-1 min-h-0 bg-white rounded-xl border border-[#dedede] p-6 sm:p-8 lg:p-10 text-[0.9375rem] leading-relaxed text-[#333] outline-none focus:border-[#00acb6] focus:ring-2 focus:ring-[#00acb6]/20 font-serif resize-none"
                placeholder="# Heading&#10;&#10;Edit the generated report in markdown…"
              />
            ) : (
              <article className="max-w-none flex-1 min-h-0 overflow-y-auto text-[#333] leading-relaxed space-y-3 bg-white rounded-xl border border-[#dedede] p-6 sm:p-8 lg:p-10 [&_h1]:font-serif [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:text-[#333] [&_h1]:mt-6 [&_h1]:mb-3 [&_h2]:font-serif [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-[#333] [&_h2]:mt-5 [&_h2]:mb-2 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-[#333] [&_h3]:mt-4 [&_h3]:mb-2 [&_p]:text-[0.9375rem] [&_p]:text-[#333] [&_ul]:pl-5 [&_ul]:list-disc [&_ul]:text-[0.9375rem] [&_ul]:text-[#333] [&_li]:mt-1">
                {renderMarkdown(detail.content_markdown || "")}
              </article>
            )}
          </div>
        )}
      </DetailDrawer>
    </>
  );
}

function formatType(type: string) { return type === "background_summary" ? "Background" : type === "cognitive_report" ? "Cognitive" : type === "unified_insights" ? "Unified" : type; }

function TypeBadge({ type }: { type: string }) {
  let cls = "bg-[#eeeeee] text-[#333]";
  if (type === "background_summary") cls = "bg-[#e6f7f8] text-[#0c888e]";
  else if (type === "cognitive_report") cls = "bg-violet-500/20 text-violet-400";
  else if (type === "unified_insights") cls = "bg-emerald-500/20 text-emerald-400";
  return <span className={`px-2 py-0.5 rounded-md text-[0.6875rem] font-medium ${cls}`}>{formatType(type)}</span>;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">{children}</th>;
}
