"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { API_BASE } from "@/lib/api";

interface Student {
  id: number;
  first_name: string;
  last_name: string;
}

interface Report {
  id: number;
  chatbot_session_id: number;
  status: string;
  created_at: string;
  profile_text: string | null;
  impact_text: string | null;
  recommendations_text: string | null;
}

interface GenerationJob {
  id: number;
  job_type: string;
  status: string;
  output_text: string | null;
}

export default function ReportsPage() {
  const router = useRouter();
  const params = useParams();
  const studentId = params.id as string;

  const [student, setStudent] = useState<Student | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [generationJobs, setGenerationJobs] = useState<GenerationJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    fetchData(token);
  }, [studentId, router]);

  const fetchData = async (token: string) => {
    try {
      // Fetch student
      const studentResponse = await fetch(
        `${API_BASE}/students/${studentId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (studentResponse.ok) {
        setStudent(await studentResponse.json());
      }

      // Fetch reports
      const reportsResponse = await fetch(
        `${API_BASE}/reports/student/${studentId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (reportsResponse.ok) {
        const reportsData = await reportsResponse.json();
        setReports(reportsData);
        if (reportsData.length > 0) {
          setSelectedReport(reportsData[0]);
        }
      } else if (reportsResponse.status === 404) {
        // No reports endpoint exists yet - that's fine, show empty state
        setReports([]);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      // On error, still show the page with empty reports
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (sessionId: number) => {
    setGenerating(true);
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE}/reports/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ chatbot_session_id: sessionId }),
      });

      if (response.ok) {
        const data = await response.json();
        setGenerationJobs(data.jobs);
        // Start polling for job status
        pollJobStatus(data.jobs, token!);
      } else {
        alert("Failed to start report generation. Please try again.");
      }
    } catch (error) {
      console.error("Error generating report:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  const pollJobStatus = async (jobs: GenerationJob[], token: string) => {
    const interval = setInterval(async () => {
      let allCompleted = true;

      for (const job of jobs) {
        const response = await fetch(
          `${API_BASE}/reports/job-status/${job.id}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        if (response.ok) {
          const jobData = await response.json();
          if (jobData.status !== "completed") {
            allCompleted = false;
          }
        }
      }

      if (allCompleted) {
        clearInterval(interval);
        // Refresh reports
        await fetchData(token);
      }
    }, 3000); // Poll every 3 seconds
  };

  const getSectionIcon = (section: string) => {
    switch (section) {
      case "profile":
        return (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        );
      case "impact":
        return (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      case "recommendations":
        return (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        );
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 font-medium">Loading reports...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push(`/student/${studentId}`)}
                className="w-10 h-10 rounded-xl bg-surface hover:bg-slate-200 transition-colors flex items-center justify-center"
              >
                <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-black text-on-background tracking-tight">
                    {student?.first_name}'s Reports
                  </h1>
                  <p className="text-xs text-slate-500 font-medium">Generated Assessments</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8 lg:py-12">
        {reports.length === 0 ? (
          <div className="glass-card p-12 rounded-2xl text-center">
            <svg className="w-20 h-20 text-slate-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-xl font-bold text-on-background mb-2">No reports yet</h3>
            <p className="text-slate-500 mb-6 max-w-md mx-auto">
              Complete an assessment first, then generate a professional report to get professional insights.
            </p>
            <button
              onClick={() => router.push(`/student/${studentId}/assessment`)}
              className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-teal-600 transition-all inline-flex items-center gap-2"
            >
              Start Assessment
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Reports List */}
            <div className="lg:col-span-1">
              <h3 className="text-lg font-bold text-on-background mb-4">Available Reports</h3>
              <div className="space-y-3">
                {reports.map((report) => (
                  <div
                    key={report.id}
                    onClick={() => setSelectedReport(report)}
                    className={`glass-card p-4 rounded-xl cursor-pointer transition-all ${
                      selectedReport?.id === report.id
                        ? "ring-2 ring-primary shadow-lg"
                        : "hover:shadow-md"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-bold text-on-background">Report #{report.id}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${
                        report.status === "approved"
                          ? "bg-emerald-100 text-emerald-700"
                          : report.status === "pending_review"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-teal-100 text-teal-700"
                      }`}>
                        {report.status.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {new Date(report.created_at).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Report Content */}
            <div className="lg:col-span-2">
              {selectedReport ? (
                <div className="space-y-6">
                  {/* Profile Section */}
                  {selectedReport.profile_text && (
                    <div className="glass-card p-8 rounded-2xl">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600">
                          {getSectionIcon("profile")}
                        </div>
                        <h3 className="text-xl font-bold text-on-background">Student Profile</h3>
                      </div>
                      <div className="prose prose-slate max-w-none">
                        <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                          {selectedReport.profile_text}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Impact Section */}
                  {selectedReport.impact_text && (
                    <div className="glass-card p-8 rounded-2xl">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600">
                          {getSectionIcon("impact")}
                        </div>
                        <h3 className="text-xl font-bold text-on-background">Educational Impact</h3>
                      </div>
                      <div className="prose prose-slate max-w-none">
                        <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                          {selectedReport.impact_text}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Recommendations Section */}
                  {selectedReport.recommendations_text && (
                    <div className="glass-card p-8 rounded-2xl">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600">
                          {getSectionIcon("recommendations")}
                        </div>
                        <h3 className="text-xl font-bold text-on-background">Recommendations</h3>
                      </div>
                      <div className="prose prose-slate max-w-none">
                        <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                          {selectedReport.recommendations_text}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Generation Jobs Status */}
                  {generationJobs.length > 0 && (
                    <div className="glass-card p-6 rounded-2xl">
                      <h4 className="font-bold text-on-background mb-4">Generation Progress</h4>
                      <div className="space-y-3">
                        {generationJobs.map((job) => (
                          <div key={job.id} className="flex items-center justify-between">
                            <span className="text-sm font-medium text-slate-700 capitalize">
                              {job.job_type} Section
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                              job.status === "completed"
                                ? "bg-emerald-100 text-emerald-700"
                                : job.status === "running"
                                ? "bg-teal-100 text-teal-700"
                                : "bg-slate-100 text-slate-700"
                            }`}>
                              {job.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="glass-card p-12 rounded-2xl text-center">
                  <p className="text-slate-500">Select a report to view details</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
