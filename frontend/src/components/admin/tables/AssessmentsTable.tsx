"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import DetailDrawer from "../DetailDrawer";
import JsonViewer from "../JsonViewer";
import type { AdminAssessmentRow } from "../types";

interface AssessmentsTableProps { rows: AdminAssessmentRow[]; }
type DrawerTab = "overview" | "context";

export default function AssessmentsTable({ rows }: AssessmentsTableProps) {
  const [selected, setSelected] = useState<AdminAssessmentRow | null>(null);
  const [detail, setDetail] = useState<AdminAssessmentRow | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [drawerTab, setDrawerTab] = useState<DrawerTab>("overview");

  const openRow = async (row: AdminAssessmentRow) => {
    setSelected(row); setDetail(null); setDrawerTab("overview"); setDetailError(null); setDetailLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(`${API_BASE}/admin/chat-sessions/${row.id}`, { headers: { Authorization: `Bearer ${token ?? ""}` } });
      if (res.ok) setDetail(await res.json()); else setDetailError(`Failed to load details (${res.status})`);
    } catch { setDetailError("Network error loading details"); } finally { setDetailLoading(false); }
  };

  const close = () => { setSelected(null); setDetail(null); setDetailError(null); };

  if (!rows || rows.length === 0) return <div className="py-12 text-center"><p className="text-sm text-slate-500">No assessments found</p></div>;

  return (
    <>
      <div className="rounded-xl overflow-hidden border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-white/5 border-b border-white/10">
              <tr><Th>Student</Th><Th>Parent Email</Th><Th>Status</Th><Th>Flow Type</Th><Th>Step</Th><Th>Started</Th><Th>Last Activity</Th></tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {rows.map((row) => (
                <tr key={row.id} onClick={() => openRow(row)} className="hover:bg-white/5 transition-colors cursor-pointer">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-white">{row.student_name || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400">{row.parent_email || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap"><StatusBadge status={row.status} /></td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400">{row.flow_type || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400">{row.current_step ?? "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-500">{row.started_at ? new Date(row.started_at).toLocaleString() : "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-500">{row.last_activity_at ? new Date(row.last_activity_at).toLocaleString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <DetailDrawer isOpen={selected !== null} onClose={close} title={selected?.student_name ? `Assessment - ${selected.student_name}` : "Assessment"}>
        {selected && (
          <div>
            <div className="flex gap-1.5 mb-4">
              <TabBtn active={drawerTab === "overview"} onClick={() => setDrawerTab("overview")}>Overview</TabBtn>
              <TabBtn active={drawerTab === "context"} onClick={() => setDrawerTab("context")}>context_data</TabBtn>
            </div>
            {detailLoading && <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-4 bg-white/5 rounded animate-pulse" />)}</div>}
            {detailError && <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-400 mb-4">{detailError}</div>}
            {!detailLoading && drawerTab === "overview" && (
              <div className="space-y-3 text-sm">
                <Row label="ID" value={selected.id} />
                <Row label="Student" value={selected.student_name || "-"} />
                <Row label="Parent Email" value={selected.parent_email || "-"} />
                <Row label="Status" value={selected.status} />
                <Row label="Flow Type" value={selected.flow_type || "-"} />
                <Row label="Current Step" value={String(selected.current_step ?? "-")} />
                <Row label="Started" value={selected.started_at ? new Date(selected.started_at).toLocaleString() : "-"} />
                <Row label="Last Activity" value={selected.last_activity_at ? new Date(selected.last_activity_at).toLocaleString() : "-"} />
              </div>
            )}
            {!detailLoading && drawerTab === "context" && <JsonViewer data={detail?.context_data ?? selected.context_data ?? {}} />}
          </div>
        )}
      </DetailDrawer>
    </>
  );
}

function StatusBadge({ status }: { status: string }) {
  const n = (status || "").toLowerCase();
  let cls = "bg-white/10 text-slate-300";
  if (n === "active" || n === "in_progress") cls = "bg-blue-500/20 text-blue-400";
  else if (n === "completed") cls = "bg-emerald-500/20 text-emerald-400";
  else if (n === "abandoned") cls = "bg-amber-500/20 text-amber-400";
  return <span className={`px-2 py-0.5 rounded-md text-[0.6875rem] font-medium ${cls}`}>{status || "-"}</span>;
}

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" onClick={onClick} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${active ? "bg-blue-600 text-white" : "bg-white/5 text-slate-400 hover:bg-white/10"}`}>{children}</button>;
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4 border-b border-white/5 pb-2"><span className="text-[0.6875rem] font-medium uppercase text-slate-500">{label}</span><span className="text-sm text-slate-300 text-right break-all">{value}</span></div>;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-slate-500 uppercase tracking-wider">{children}</th>;
}
