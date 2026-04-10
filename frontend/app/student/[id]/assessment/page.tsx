"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { API_BASE } from "@/lib/api";

export default function AssessmentStartPage() {
  const router = useRouter();
  const params = useParams();
  const studentId = params.id as string;
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const startAssessment = async () => {
      try {
        console.log("Starting assessment for student:", studentId);
        const token = localStorage.getItem("access_token");
        console.log("Token found:", !!token);

        if (!token) {
          console.log("No token, redirecting to login");
          router.push("/login");
          return;
        }

        console.log("Making POST request to start session");
        // Start or resume assessment session
        const response = await fetch(`${API_BASE}/chatbot/sessions/start`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({
            student_id: studentId,
          }),
        });

        console.log("Response status:", response.status);

        if (response.ok) {
          const session = await response.json();
          console.log("Session created:", session);
          // Redirect to assessment page with token
          router.push(`/student/${studentId}/assessment/${session.resume_token}`);
        } else if (response.status === 401) {
          console.log("Unauthorized, redirecting to login");
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          router.push("/login");
        } else {
          const errorData = await response.json();
          console.error("Error response:", errorData);
          setError(errorData.detail || "Failed to start assessment");
          setLoading(false);
        }
      } catch (err) {
        console.error("Error starting assessment:", err);
        setError(`An error occurred. Please try again. ${err instanceof Error ? err.message : ''}`);
        setLoading(false);
      }
    };

    startAssessment();
  }, [studentId, router]);

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-teal-600 transition-all"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-spin">
          <svg
            className="w-8 h-8 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Starting Assessment...
        </h2>
        <p className="text-gray-600">
          Please wait while we prepare the assessment session.
        </p>
      </div>
    </div>
  );
}
