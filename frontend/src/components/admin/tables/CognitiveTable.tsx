"use client";

import { useState } from "react";
import DetailDrawer from "../DetailDrawer";
import JsonViewer from "../JsonViewer";
import type { AdminCognitiveRow } from "../types";

interface CognitiveTableProps { rows: AdminCognitiveRow[]; }

export default function CognitiveTable({ rows }: CognitiveTableProps) {
  const [selected, setSelected] = useState<AdminCognitiveRow | null>(null);

  if (!rows || rows.length === 0) return <div className="py-12 text-center"><p className="text-sm text-[#737373]">No cognitive profiles found</p></div>;

  return (
    <>
      <div className="rounded-xl overflow-hidden border border-[#dedede]">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#f4f4f4] border-b border-[#dedede]">
              <tr><Th>Student</Th><Th>Test Name</Th><Th>Test Date</Th><Th>Overall Score</Th><Th>Quality</Th><Th>Text Length</Th><Th>Created</Th></tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {rows.map((row) => {
                const fsiq = row.parsed_scores?.full_scale_iq ?? null;
                return (
                  <tr key={row.id} onClick={() => setSelected(row)} className="hover:bg-[#f4f4f4] transition-colors cursor-pointer">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#333]">{row.student_name || "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.test_name || "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.test_date ? new Date(row.test_date).toLocaleDateString() : "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#333]">{fsiq ?? "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap"><ConfBadge confidence={row.confidence} review={row.requires_review} /></td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.ocr_text_length ?? "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.created_at ? new Date(row.created_at).toLocaleDateString() : "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      <DetailDrawer isOpen={selected !== null} onClose={() => setSelected(null)} title={selected?.student_name ? `Cognitive - ${selected.student_name}` : "Cognitive Profile"}>
        {selected && <div><h4 className="text-[0.6875rem] font-medium uppercase text-[#737373] mb-2">parsed_scores</h4><JsonViewer data={selected.parsed_scores ?? {}} /></div>}
      </DetailDrawer>
    </>
  );
}

function ConfBadge({ confidence, review }: { confidence: number | null | undefined; review: boolean | null | undefined }) {
  if (confidence === null || confidence === undefined) return <span className="text-sm text-slate-600">-</span>;
  let cls = "bg-red-500/20 text-red-400";
  if (confidence >= 0.9) cls = "bg-emerald-500/20 text-emerald-400";
  else if (confidence >= 0.7) cls = "bg-amber-500/20 text-amber-400";
  return <span className={`px-2 py-0.5 rounded-md text-[0.6875rem] font-medium ${cls}`}>{(confidence * 100).toFixed(0)}%{review ? " - review" : ""}</span>;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">{children}</th>;
}
