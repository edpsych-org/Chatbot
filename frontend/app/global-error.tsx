"use client";

import { useEffect } from "react";
import { reportClientError } from "@/src/lib/logger";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    reportClientError(error, { digest: error.digest, boundary: "global" });
  }, [error]);

  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, padding: 0 }}>
        <div
          style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#f8fafc",
            padding: "1rem",
          }}
        >
          <div
            style={{
              maxWidth: 420,
              background: "white",
              padding: "2rem",
              borderRadius: 16,
              boxShadow: "0 10px 25px rgba(0,0,0,0.06)",
              textAlign: "center",
            }}
          >
            <h2 style={{ fontSize: 20, fontWeight: 700, color: "#1e293b", marginBottom: 8 }}>
              Application error
            </h2>
            <p style={{ fontSize: 14, color: "#64748b", marginBottom: 20 }}>
              An unexpected error occurred. It has been logged for the team.
            </p>
            <button
              onClick={reset}
              style={{
                padding: "10px 20px",
                background: "#00acb6",
                color: "white",
                fontWeight: 700,
                borderRadius: 12,
                border: "none",
                cursor: "pointer",
              }}
            >
              Try again
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
