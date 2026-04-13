"use client";

import { useState } from "react";
import DetailDrawer from "../DetailDrawer";
import JsonViewer from "../JsonViewer";
import type { AdminStudentRow } from "../types";

interface StudentsTableProps { rows: AdminStudentRow[]; }

export default function StudentsTable({ rows }: StudentsTableProps) {
  const [selected, setSelected] = useState<AdminStudentRow | null>(null);

  if (!rows || rows.length === 0) return <EmptyState label="students" />;

  return (
    <>
      <div className="rounded-xl overflow-hidden border border-[#dedede]">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#f4f4f4] border-b border-[#dedede]">
              <tr><Th>Name</Th><Th>Grade</Th><Th>School</Th><Th>Primary Guardian</Th><Th>Sessions</Th><Th>Created</Th></tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {rows.map((row) => (
                <tr key={row.id} onClick={() => setSelected(row)} className="hover:bg-[#f4f4f4] transition-colors cursor-pointer">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#333]">{row.first_name} {row.last_name}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.grade_level || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.school_name || "-"}</td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {row.primary_guardian ? (
                      <div>
                        <p className="text-sm font-medium text-[#333]">{row.primary_guardian.name}</p>
                        <p className="text-[0.6875rem] text-[#737373]">{row.primary_guardian.email}</p>
                      </div>
                    ) : <span className="text-sm text-slate-600">-</span>}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.sessions_count ?? 0}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.created_at ? new Date(row.created_at).toLocaleDateString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <DetailDrawer isOpen={selected !== null} onClose={() => setSelected(null)} title={selected ? `${selected.first_name} ${selected.last_name}` : "Student"}>
        {selected && <JsonViewer data={selected} />}
      </DetailDrawer>
    </>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">{children}</th>;
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="py-12 text-center">
      <p className="text-sm text-[#737373]">No {label} found</p>
    </div>
  );
}
