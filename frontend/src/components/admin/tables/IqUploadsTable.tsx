"use client";

import type { AdminIqUploadRow } from "../types";

interface IqUploadsTableProps { rows: AdminIqUploadRow[]; }

export default function IqUploadsTable({ rows }: IqUploadsTableProps) {
  return (
    <>
      <div className="mb-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm text-blue-300">
        Original PDFs are deleted after extraction for privacy. Only metadata and parsed scores are retained.
      </div>

      {!rows || rows.length === 0 ? (
        <div className="py-12 text-center"><p className="text-sm text-slate-500">No IQ uploads found</p></div>
      ) : (
        <div className="rounded-xl overflow-hidden border border-white/10">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/10">
                <tr><Th>Student</Th><Th>Filename</Th><Th>Size</Th><Th>Status</Th><Th>Uploaded By</Th><Th>Uploaded At</Th></tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {rows.map((row) => (
                  <tr key={row.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-white">{row.student_name || "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400 font-mono">{row.filename}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400">{formatBytes(row.file_size)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-400">{row.status || "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {row.uploaded_by_name ? (
                        <div>
                          <p className="text-sm font-medium text-slate-300">{row.uploaded_by_name}</p>
                          {row.uploaded_by_email && <p className="text-[0.6875rem] text-slate-500">{row.uploaded_by_email}</p>}
                        </div>
                      ) : <span className="text-sm text-slate-600">-</span>}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-500">{row.uploaded_at || row.created_at ? new Date((row.uploaded_at || row.created_at) as string).toLocaleString() : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-slate-500 uppercase tracking-wider">{children}</th>;
}
