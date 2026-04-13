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

  if (!rows || rows.length === 0) return <div className="py-12 text-center"><p className="text-sm text-[#737373]">No assessments found</p></div>;

  return (
    <>
      <div className="rounded-xl overflow-hidden border border-[#dedede]">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#f4f4f4] border-b border-[#dedede]">
              <tr><Th>Student</Th><Th>Parent Email</Th><Th>Status</Th><Th>Flow Type</Th><Th>Step</Th><Th>Started</Th><Th>Last Activity</Th></tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {rows.map((row) => (
                <tr key={row.id} onClick={() => openRow(row)} className="hover:bg-[#f4f4f4] transition-colors cursor-pointer">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#333]">{row.student_name || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.parent_email || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap"><StatusBadge status={row.status} /></td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.flow_type || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.current_step ?? "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.started_at ? new Date(row.started_at).toLocaleString() : "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.last_activity_at ? new Date(row.last_activity_at).toLocaleString() : "-"}</td>
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
            {detailLoading && <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-4 bg-[#f4f4f4] rounded animate-pulse" />)}</div>}
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
  let cls = "bg-[#eeeeee] text-[#333]";
  if (n === "active" || n === "in_progress") cls = "bg-[#e6f7f8] text-[#0c888e]";
  else if (n === "completed") cls = "bg-emerald-500/20 text-emerald-400";
  else if (n === "abandoned") cls = "bg-amber-500/20 text-amber-400";
  return <span className={`px-2 py-0.5 rounded-md text-[0.6875rem] font-medium ${cls}`}>{status || "-"}</span>;
}

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" onClick={onClick} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${active ? "bg-[#00acb6] text-[#333]" : "bg-[#f4f4f4] text-[#737373] hover:bg-[#eeeeee]"}`}>{children}</button>;
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-4 border-b border-[#dedede] pb-2"><span className="text-[0.6875rem] font-medium uppercase text-[#737373]">{label}</span><span className="text-sm text-[#333] text-right break-all">{value}</span></div>;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">{children}</th>;
}
