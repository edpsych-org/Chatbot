"use client";

import type { AdminIqUploadRow } from "../types";

interface IqUploadsTableProps { rows: AdminIqUploadRow[]; }

export default function IqUploadsTable({ rows }: IqUploadsTableProps) {
  return (
    <>
      <div className="mb-4 p-3 rounded-lg bg-[#e6f7f8] border border-[#00acb6]/40 text-sm text-[#0c888e]">
        Original PDFs are deleted after extraction for privacy. Only metadata and parsed scores are retained.
      </div>

      {!rows || rows.length === 0 ? (
        <div className="py-12 text-center"><p className="text-sm text-[#737373]">No IQ uploads found</p></div>
      ) : (
        <div className="rounded-xl overflow-hidden border border-[#dedede]">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#f4f4f4] border-b border-[#dedede]">
                <tr><Th>Student</Th><Th>Filename</Th><Th>Size</Th><Th>Status</Th><Th>Uploaded By</Th><Th>Uploaded At</Th></tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {rows.map((row) => (
                  <tr key={row.id} className="hover:bg-[#f4f4f4] transition-colors">
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[#333]">{row.student_name || "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373] font-mono">{row.filename}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{formatBytes(row.file_size)}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.status || "-"}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {row.uploaded_by_name ? (
                        <div>
                          <p className="text-sm font-medium text-[#333]">{row.uploaded_by_name}</p>
                          {row.uploaded_by_email && <p className="text-[0.6875rem] text-[#737373]">{row.uploaded_by_email}</p>}
                        </div>
                      ) : <span className="text-sm text-slate-600">-</span>}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[#737373]">{row.uploaded_at || row.created_at ? new Date((row.uploaded_at || row.created_at) as string).toLocaleString() : "-"}</td>
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
  return <th className="px-4 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">{children}</th>;
}
