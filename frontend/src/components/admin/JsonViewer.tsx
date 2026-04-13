"use client";

import { useState } from "react";

interface JsonViewerProps {
  data: any;
}

export default function JsonViewer({ data }: JsonViewerProps) {
  const [copied, setCopied] = useState(false);

  let jsonString = "";
  try { jsonString = JSON.stringify(data, null, 2); } catch { jsonString = String(data); }

  const handleCopy = async () => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(jsonString);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }
    } catch {}
  };

  return (
    <div className="relative">
      <button type="button" onClick={handleCopy} className="absolute top-2 right-2 z-10 px-3 py-1 text-[0.6875rem] font-medium rounded-md bg-[#eeeeee] text-[#333] hover:bg-[#dedede] transition-colors">
        {copied ? "Copied!" : "Copy"}
      </button>
      <pre className="bg-[#f4f4f4] text-[#333] p-4 rounded-xl overflow-auto max-h-[70vh] text-xs font-mono whitespace-pre border border-[#dedede]">
        {jsonString}
      </pre>
    </div>
  );
}
