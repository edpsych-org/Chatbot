"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";
import DetailDrawer from "../DetailDrawer";
import JsonViewer from "../JsonViewer";
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

  const close = () => { setSelected(null); setDetail(null); setDetailError(null); };

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
          <div className="space-y-6">
            <div>
              <h4 className="text-[0.6875rem] font-medium uppercase text-[#737373] mb-2">content_markdown</h4>
              <pre className="bg-[#f4f4f4] border border-[#dedede] rounded-xl p-4 whitespace-pre-wrap font-mono text-sm text-[#333] max-h-[50vh] overflow-auto">{detail.content_markdown || "(empty)"}</pre>
            </div>
            <div>
              <h4 className="text-[0.6875rem] font-medium uppercase text-[#737373] mb-2">source_data</h4>
              <JsonViewer data={detail.source_data ?? {}} />
            </div>
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
