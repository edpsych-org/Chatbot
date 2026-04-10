"use client";

import { useRef, useState } from "react";
import { API_BASE } from "@/lib/api";
import type { CognitiveProfile } from "./types";

interface PdfUploadZoneProps {
  studentId: string;
  onUploaded: (profile: CognitiveProfile) => void;
  disabled?: boolean;
}

const MAX_BYTES = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPES = ["application/pdf", "image/png", "image/jpeg", "image/jpg"];
const ALLOWED_EXT = /\.(pdf|png|jpe?g)$/i;

export default function PdfUploadZone({
  studentId,
  onUploaded,
  disabled = false,
}: PdfUploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = (file: File): string | null => {
    if (file.size > MAX_BYTES) return "File is larger than 10 MB.";
    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXT.test(file.name)) {
      return "Unsupported file type. Please upload a PDF, PNG, or JPEG.";
    }
    return null;
  };

  const uploadFile = (file: File) => {
    const err = validate(file);
    if (err) {
      setError(err);
      return;
    }
    setError(null);

    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("You are not signed in. Please log in again.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open(
      "POST",
      `${API_BASE}/psychologist-reports/students/${studentId}/cognitive-report/upload`
    );
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        setProgress(pct);
      }
    };

    xhr.upload.onload = () => {
      // Upload bytes done; backend is now extracting + running LLM
      setProcessing(true);
    };

    xhr.onload = () => {
      setUploading(false);
      setProcessing(false);
      setProgress(0);
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const body = JSON.parse(xhr.responseText);
          // Backend returns { ocr_used, confidence_score, cognitive_profile: {...} }
          const profile = (body.cognitive_profile ?? body) as CognitiveProfile;
          onUploaded(profile);
        } catch {
          setError("Upload succeeded but response was invalid.");
        }
      } else {
        let detail = `Upload failed (${xhr.status})`;
        try {
          const body = JSON.parse(xhr.responseText);
          if (body?.detail) detail = body.detail;
        } catch {
          /* ignore */
        }
        setError(detail);
      }
    };

    xhr.onerror = () => {
      setUploading(false);
      setProcessing(false);
      setProgress(0);
      setError("Network error during upload. Please try again.");
    };

    setUploading(true);
    setProgress(0);
    xhr.send(formData);
  };

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (disabled || uploading) return;
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled || uploading) return;
    setDragActive(true);
  };

  const onDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleBrowse = () => {
    if (disabled || uploading) return;
    inputRef.current?.click();
  };

  return (
    <div>
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={handleBrowse}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") handleBrowse();
        }}
        className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
          disabled || uploading
            ? "opacity-60 cursor-not-allowed"
            : dragActive
            ? "border-primary bg-teal-50"
            : "border-slate-300 bg-slate-50 hover:border-primary hover:bg-teal-50/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,image/png,image/jpeg,image/jpg"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) uploadFile(file);
            e.target.value = "";
          }}
        />

        {!uploading && !processing && (
          <>
            <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-500 flex items-center justify-center text-white">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.9 5 5 0 019.9-1A5 5 0 0118 16M12 12v9m0-9l-3 3m3-3l3 3"
                />
              </svg>
            </div>
            <p className="text-sm font-semibold text-slate-800">
              Drop a Cognitive Report PDF here, or <span className="text-primary underline">click to browse</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">PDF, PNG, or JPEG · up to 10 MB</p>
          </>
        )}

        {uploading && !processing && (
          <div>
            <p className="text-sm font-semibold text-slate-700 mb-3">
              Uploading… {progress}%
            </p>
            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-primary h-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {processing && (
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-sm font-semibold text-slate-700">
              Processing PDF and extracting scores…
            </p>
            <p className="text-xs text-slate-500 mt-1">
              This may take 10–30 seconds to process.
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm font-medium text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}
