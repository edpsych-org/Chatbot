"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { API_BASE } from "@/lib/api";

interface Recipient {
  user_id: string;
  name: string;
  email: string;
  relationship: string;
}

interface PreviouslyShared {
  sent_at: string | null;
  recipient_email: string | null;
  recipient_name: string | null;
  relationship: string | null;
}

interface PreviewResponse {
  school_session: {
    session_id: string;
    completed_at: string | null;
    answers_count: number;
  } | null;
  recipients: Recipient[];
  previously_shared: PreviouslyShared[];
}

interface SchoolShareButtonProps {
  studentId: string;
  studentName: string;
}

export default function SchoolShareButton({ studentId, studentName }: SchoolShareButtonProps) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => { setMounted(true); }, []);

  const fetchPreview = useCallback(async () => {
    setLoading(true);
    setError(null);
    setPreview(null);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(`${API_BASE}/admin/students/${studentId}/school-share/preview`, {
        headers: { Authorization: `Bearer ${token ?? ""}` },
      });
      if (!res.ok) {
        let msg = `Failed to load (${res.status})`;
        try { const b = await res.json(); if (b?.detail) msg = typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail); } catch { /* ignore */ }
        throw new Error(msg);
      }
      const data: PreviewResponse = await res.json();
      setPreview(data);
      if (data.recipients.length > 0) setSelectedUserId(data.recipients[0].user_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  const onOpen = () => {
    setOpen(true);
    setNote("");
    setSendError(null);
    setToast(null);
    fetchPreview();
  };

  const onClose = () => {
    if (sending) return;
    setOpen(false);
  };

  const onSend = async () => {
    if (!preview?.school_session || !selectedUserId || sending) return;
    setSending(true);
    setSendError(null);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
      const res = await fetch(`${API_BASE}/admin/students/${studentId}/school-share/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token ?? ""}`,
        },
        body: JSON.stringify({ recipient_user_id: selectedUserId, note: note.trim() || undefined }),
      });
      if (!res.ok && res.status !== 202) {
        let msg = `Send failed (${res.status})`;
        try {
          const b = await res.json();
          if (b?.detail) {
            if (typeof b.detail === "string") msg = b.detail;
            else if (b.detail?.detail) msg = `${b.detail.detail}${b.detail.provider_error ? ` — ${b.detail.provider_error}` : ""}`;
            else msg = JSON.stringify(b.detail);
          }
        } catch { /* ignore */ }
        throw new Error(msg);
      }
      const data = await res.json();
      setToast(`Sent to ${data.recipient_email}`);
      setNote("");
      await fetchPreview();
      setTimeout(() => setToast(null), 3500);
    } catch (e) {
      setSendError(e instanceof Error ? e.message : "Send failed");
    } finally {
      setSending(false);
    }
  };

  const label = "Share school input";

  return (
    <>
      <button
        type="button"
        onClick={onOpen}
        title={label}
        className="h-7 px-2 text-[0.6875rem] font-medium text-[#0c888e] border border-[#dedede] hover:border-[#00acb6] hover:bg-[#e6f7f8] rounded inline-flex items-center gap-1"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l9 6 9-6M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        School share
      </button>

      {open && mounted && createPortal(
        <div className="fixed inset-0 z-[110] flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
          <div className="relative w-full max-w-lg bg-white rounded-xl shadow-2xl border border-[#dedede] max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#dedede]">
              <div className="min-w-0">
                <h3 className="text-base font-semibold text-[#333] truncate">
                  Email school input
                </h3>
                <p className="text-[0.75rem] text-[#737373] truncate">{studentName}</p>
              </div>
              <button type="button" onClick={onClose} aria-label="Close" className="w-8 h-8 rounded-lg flex items-center justify-center text-[#737373] hover:bg-[#eeeeee] hover:text-[#333]">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>

            <div className="flex-1 min-h-0 overflow-y-auto px-5 py-4 space-y-4 text-sm">
              {loading && (
                <div className="space-y-2">
                  <div className="h-4 bg-[#f4f4f4] rounded animate-pulse" />
                  <div className="h-4 bg-[#f4f4f4] rounded animate-pulse w-3/4" />
                </div>
              )}

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600">
                  {error}
                </div>
              )}

              {!loading && !error && preview && !preview.school_session && (
                <div className="p-4 bg-[#f4f4f4] rounded-lg text-[#737373]">
                  No completed school input for this student yet.
                </div>
              )}

              {!loading && !error && preview?.school_session && (
                <>
                  <div className="p-3 rounded-lg bg-[#e6f7f8] border border-[#00acb6]/30 text-[0.8125rem] text-[#0c888e]">
                    <div className="font-semibold">School input ready to share</div>
                    <div className="text-[0.75rem] text-[#0c888e]/80 mt-0.5">
                      Completed {preview.school_session.completed_at ? new Date(preview.school_session.completed_at).toLocaleDateString() : "—"}
                      {" · "}{preview.school_session.answers_count} answers
                    </div>
                  </div>

                  <div>
                    <label className="block text-[0.75rem] font-semibold text-[#333] mb-1">Recipient</label>
                    {preview.recipients.length === 0 ? (
                      <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-[0.8125rem] text-amber-700">
                        No parent/guardian email on file for this student. Add a guardian first.
                      </div>
                    ) : (
                      <select
                        value={selectedUserId}
                        onChange={(e) => setSelectedUserId(e.target.value)}
                        className="w-full px-3 py-2 bg-white border border-[#dedede] rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6]"
                      >
                        {preview.recipients.map((r) => (
                          <option key={r.user_id} value={r.user_id}>
                            {r.relationship} — {r.name} ({r.email})
                          </option>
                        ))}
                      </select>
                    )}
                  </div>

                  <div>
                    <label className="block text-[0.75rem] font-semibold text-[#333] mb-1">
                      Optional note
                      <span className="ml-2 text-[0.6875rem] font-normal text-[#737373]">
                        {note.length}/500
                      </span>
                    </label>
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value.slice(0, 500))}
                      rows={3}
                      placeholder="Shown in the email body. Optional."
                      className="w-full px-3 py-2 bg-white border border-[#dedede] rounded-lg text-sm outline-none focus:ring-2 focus:ring-[#00acb6]/20 focus:border-[#00acb6] resize-none"
                    />
                  </div>

                  <div className="text-[0.75rem] text-[#737373]">
                    Attachment: <code className="font-mono text-[#333]">{studentName.replace(/[^A-Za-z0-9]/g, "") || "Student"}_school_input.pdf</code> (generated on send)
                  </div>

                  {preview.previously_shared.length > 0 && (
                    <div className="pt-3 border-t border-[#eeeeee]">
                      <div className="text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider mb-1.5">Previously shared</div>
                      <ul className="space-y-1 text-[0.75rem] text-[#333]">
                        {preview.previously_shared.map((p, idx) => (
                          <li key={idx}>
                            · {p.sent_at ? new Date(p.sent_at).toLocaleString() : "—"}
                            {" → "}
                            {p.recipient_email || "—"}
                            {p.relationship ? ` (${p.relationship})` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {sendError && (
                    <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-[0.8125rem] text-red-600">
                      {sendError}
                    </div>
                  )}

                  {toast && (
                    <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-[0.8125rem] text-emerald-700">
                      {toast}
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-[#dedede] bg-[#f9f9f9]">
              <button
                type="button"
                onClick={onClose}
                disabled={sending}
                className="px-4 py-2 text-sm font-medium text-[#333] bg-white border border-[#dedede] hover:bg-[#f4f4f4] rounded-lg disabled:opacity-50"
              >
                {toast ? "Close" : "Cancel"}
              </button>
              <button
                type="button"
                onClick={onSend}
                disabled={
                  sending ||
                  loading ||
                  !preview?.school_session ||
                  !selectedUserId ||
                  (preview?.recipients?.length ?? 0) === 0
                }
                className="px-4 py-2 text-sm font-semibold text-white bg-[#00acb6] hover:bg-[#0c888e] rounded-lg disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center gap-2"
              >
                {sending && (
                  <span className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin" />
                )}
                {sending ? "Sending…" : "Send email"}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
