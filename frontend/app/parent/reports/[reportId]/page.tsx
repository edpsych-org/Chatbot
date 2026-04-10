'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';

import { API_BASE } from '@/lib/api';

interface ReportData {
  id: string;
  student_id: string;
  session_id: string;
  profile_text: string | null;
  impact_text: string | null;
  recommendations_text: string | null;
  status: string;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

interface ReportDetailedResponse {
  report: ReportData;
  profile_job: unknown;
  impact_job: unknown;
  recommendations_job: unknown;
  reviews: Array<{
    id: string;
    review_status: string;
    edited_profile_text: string | null;
    edited_impact_text: string | null;
    edited_recommendations_text: string | null;
    reviewer_notes: string | null;
    reviewed_at: string;
  }>;
}

interface StudentInfo {
  id: string;
  first_name: string;
  last_name: string;
  grade_level?: string;
  school_name?: string;
  year_group?: string;
}

function formatTextToParagraphs(text: string | null): React.ReactNode[] {
  if (!text) return [];
  return text
    .split('\n')
    .filter((line) => line.trim().length > 0)
    .map((paragraph, index) => (
      <p key={index} className="mb-4 last:mb-0">
        {paragraph.trim()}
      </p>
    ));
}

export default function ParentReportViewPage() {
  const router = useRouter();
  const params = useParams();
  const reportId = params.reportId as string;

  const [reportData, setReportData] = useState<ReportDetailedResponse | null>(null);
  const [student, setStudent] = useState<StudentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notApproved, setNotApproved] = useState(false);

  const getToken = useCallback(() => {
    return localStorage.getItem('token');
  }, []);

  useEffect(() => {
    const token = getToken();
    const userData = localStorage.getItem('user');

    if (!token || !userData) {
      router.push('/login');
      return;
    }

    const fetchReport = async () => {
      try {
        const response = await fetch(`${API_BASE}/reports/${reportId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const data: ReportDetailedResponse = await response.json();

          // Only show if report is approved
          if (data.report.status !== 'approved') {
            setNotApproved(true);
            setLoading(false);
            return;
          }

          setReportData(data);

          // Fetch student info
          if (data.report.student_id) {
            const studentRes = await fetch(
              `${API_BASE}/students/${data.report.student_id}`,
              { headers: { Authorization: `Bearer ${token}` } }
            );
            if (studentRes.ok) {
              setStudent(await studentRes.json());
            }
          }
        } else if (response.status === 401) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          router.push('/login');
        } else if (response.status === 404) {
          setError('Report not found.');
        } else {
          setError('Failed to load report.');
        }
      } catch (err) {
        console.error('Error fetching report:', err);
        setError('Network error. Please check your connection.');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [reportId, router, getToken]);

  // Determine which text to show: edited (from latest approved review) or original
  const getDisplayText = (
    section: 'profile' | 'impact' | 'recommendations'
  ): string | null => {
    if (!reportData) return null;

    // Check for latest approved review with edited text
    const approvedReview = reportData.reviews.find(
      (r) => r.review_status === 'approved'
    );

    if (approvedReview) {
      const editedField =
        section === 'profile'
          ? approvedReview.edited_profile_text
          : section === 'impact'
          ? approvedReview.edited_impact_text
          : approvedReview.edited_recommendations_text;

      if (editedField) return editedField;
    }

    // Fall back to original generated text
    const report = reportData.report;
    switch (section) {
      case 'profile':
        return report.profile_text;
      case 'impact':
        return report.impact_text;
      case 'recommendations':
        return report.recommendations_text;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 font-medium">Loading report...</p>
        </div>
      </div>
    );
  }

  if (notApproved) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <svg
            className="w-20 h-20 text-amber-400 mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h2 className="text-2xl font-bold text-on-background mb-3">
            Report Not Yet Available
          </h2>
          <p className="text-slate-500 mb-8">
            This report is still being reviewed by the psychologist. You will be
            able to view it once it has been approved.
          </p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-teal-600 transition-all min-h-[44px]"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <svg
            className="w-16 h-16 text-red-400 mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          <h2 className="text-xl font-bold text-on-background mb-2">Error</h2>
          <p className="text-slate-500 mb-6">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-teal-600 transition-all min-h-[44px]"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!reportData) return null;

  const studentName = student
    ? `${student.first_name} ${student.last_name}`
    : 'Student';
  const reportDate = new Date(reportData.report.created_at).toLocaleDateString(
    'en-GB',
    {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }
  );

  const profileText = getDisplayText('profile');
  const impactText = getDisplayText('impact');
  const recommendationsText = getDisplayText('recommendations');

  return (
    <>
      {/* Print-friendly styles */}
      <style jsx global>{`
        @media print {
          header,
          .no-print {
            display: none !important;
          }
          body {
            background: white !important;
          }
          .print-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
          }
          .glass-card {
            background: white !important;
            backdrop-filter: none !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: none !important;
            break-inside: avoid;
          }
          .noise-overlay {
            display: none !important;
          }
          .report-section {
            page-break-inside: avoid;
          }
        }
      `}</style>

      <div className="min-h-screen bg-background">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-40 no-print">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="w-10 h-10 rounded-xl bg-surface hover:bg-slate-200 transition-colors flex items-center justify-center min-w-[44px] min-h-[44px]"
                  aria-label="Back to dashboard"
                >
                  <svg
                    className="w-5 h-5 text-slate-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 19l-7-7 7-7"
                    />
                  </svg>
                </button>
                <div>
                  <h1 className="text-lg sm:text-xl font-black text-on-background tracking-tight">
                    Assessment Report
                  </h1>
                  <p className="text-xs text-slate-500 font-medium">
                    {studentName}
                  </p>
                </div>
              </div>
              <button
                onClick={() => window.print()}
                className="px-4 py-2 bg-surface text-slate-700 text-sm font-bold rounded-xl hover:bg-slate-200 transition-all min-h-[44px] inline-flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
                  />
                </svg>
                Print
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12 print-container">
          {/* Report Title Block */}
          <div className="text-center mb-8 sm:mb-12">
            <h2
              className="text-2xl sm:text-3xl font-extrabold text-on-background mb-2"
              style={{ fontFamily: 'Georgia, "Times New Roman", Times, serif' }}
            >
              Assessment Report - {studentName}
            </h2>
            <p className="text-slate-500 text-sm">{reportDate}</p>
            <div className="mt-3">
              <span className="px-3 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded-lg">
                APPROVED
              </span>
            </div>
          </div>

          <div className="space-y-6 sm:space-y-8">
            {/* Profile Section */}
            {profileText && (
              <section className="glass-card p-6 sm:p-8 rounded-2xl report-section">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600 flex-shrink-0">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                  </div>
                  <h3
                    className="text-xl font-bold text-on-background"
                    style={{
                      fontFamily:
                        'Georgia, "Times New Roman", Times, serif',
                    }}
                  >
                    About {student?.first_name || 'Student'}
                  </h3>
                </div>
                <div
                  className="text-slate-700 leading-relaxed text-base"
                  style={{
                    fontFamily: 'Georgia, "Times New Roman", Times, serif',
                  }}
                >
                  {formatTextToParagraphs(profileText)}
                </div>
              </section>
            )}

            {/* Impact Section */}
            {impactText && (
              <section className="glass-card p-6 sm:p-8 rounded-2xl report-section">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-10 h-10 rounded-xl bg-teal-100 flex items-center justify-center text-teal-600 flex-shrink-0">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <h3
                    className="text-xl font-bold text-on-background"
                    style={{
                      fontFamily:
                        'Georgia, "Times New Roman", Times, serif',
                    }}
                  >
                    Assessment Findings
                  </h3>
                </div>
                <div
                  className="text-slate-700 leading-relaxed text-base"
                  style={{
                    fontFamily: 'Georgia, "Times New Roman", Times, serif',
                  }}
                >
                  {formatTextToParagraphs(impactText)}
                </div>
              </section>
            )}

            {/* Recommendations Section */}
            {recommendationsText && (
              <section className="glass-card p-6 sm:p-8 rounded-2xl report-section">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600 flex-shrink-0">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                  </div>
                  <h3
                    className="text-xl font-bold text-on-background"
                    style={{
                      fontFamily:
                        'Georgia, "Times New Roman", Times, serif',
                    }}
                  >
                    Recommendations
                  </h3>
                </div>
                <div
                  className="text-slate-700 leading-relaxed text-base"
                  style={{
                    fontFamily: 'Georgia, "Times New Roman", Times, serif',
                  }}
                >
                  {formatTextToParagraphs(recommendationsText)}
                </div>
              </section>
            )}

            {/* No content fallback */}
            {!profileText && !impactText && !recommendationsText && (
              <div className="glass-card p-12 rounded-2xl text-center">
                <p className="text-slate-500">
                  No report content is available at this time.
                </p>
              </div>
            )}
          </div>

          {/* Back Button */}
          <div className="mt-8 pb-8 no-print">
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-3 bg-surface text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition-all min-h-[44px]"
            >
              Back to Dashboard
            </button>
          </div>
        </main>
      </div>
    </>
  );
}
