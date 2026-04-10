'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';

import { API_BASE } from '@/lib/api';
import ConfirmModal from '@/components/ConfirmModal';
import { useConfirm } from '@/hooks/useConfirm';

interface JobInfo {
  id: string;
  job_type: string;
  status: string;
  output_text: string | null;
  error_message: string | null;
}

interface ReviewInfo {
  id: string;
  review_status: string;
  reviewer_notes: string | null;
  reviewed_at: string;
}

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
  profile_job: JobInfo | null;
  impact_job: JobInfo | null;
  recommendations_job: JobInfo | null;
  reviews: ReviewInfo[];
}

interface StudentInfo {
  id: string;
  first_name: string;
  last_name: string;
  grade_level?: string;
  school_name?: string;
  year_group?: string;
}

export default function PsychologistReportReviewPage() {
  const router = useRouter();
  const params = useParams();
  const reportId = params.reportId as string;

  const [reportData, setReportData] = useState<ReportDetailedResponse | null>(null);
  const [student, setStudent] = useState<StudentInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const { confirm, confirmProps } = useConfirm();

  // Editable fields
  const [editedProfile, setEditedProfile] = useState('');
  const [editedImpact, setEditedImpact] = useState('');
  const [editedRecommendations, setEditedRecommendations] = useState('');
  const [reviewerNotes, setReviewerNotes] = useState('');

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  const getToken = useCallback(() => {
    return localStorage.getItem('token');
  }, []);

  const fetchReport = useCallback(async (token: string) => {
    try {
      const response = await fetch(`${API_BASE}/reports/${reportId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data: ReportDetailedResponse = await response.json();
        setReportData(data);

        // Pre-fill editable fields with the latest text
        setEditedProfile(data.report.profile_text || '');
        setEditedImpact(data.report.impact_text || '');
        setEditedRecommendations(data.report.recommendations_text || '');

        // Fetch student info
        if (data.report.student_id) {
          const studentRes = await fetch(`${API_BASE}/students/${data.report.student_id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (studentRes.ok) {
            setStudent(await studentRes.json());
          }
        }

        return data;
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
    return null;
  }, [reportId, router]);

  const hasRunningJobs = useCallback((data: ReportDetailedResponse | null): boolean => {
    if (!data) return false;
    const jobs = [data.profile_job, data.impact_job, data.recommendations_job];
    return jobs.some((job) => job && (job.status === 'pending' || job.status === 'running'));
  }, []);

  useEffect(() => {
    const token = getToken();
    const userData = localStorage.getItem('user');

    if (!token || !userData) {
      router.push('/login');
      return;
    }

    const parsedUser = JSON.parse(userData);
    if (parsedUser.role.toUpperCase() !== 'PSYCHOLOGIST') {
      router.push('/dashboard');
      return;
    }

    fetchReport(token).then((data) => {
      // Start polling if jobs are still running
      if (hasRunningJobs(data)) {
        pollingRef.current = setInterval(async () => {
          const freshToken = getToken();
          if (!freshToken) return;
          const refreshed = await fetchReport(freshToken);
          if (!hasRunningJobs(refreshed)) {
            if (pollingRef.current) {
              clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
          }
        }, 5000);
      }
    });

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, [router, getToken, fetchReport, hasRunningJobs]);

  const handleSaveChanges = async () => {
    const token = getToken();
    if (!token) return;

    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/reports/${reportId}/review`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          review_status: 'changes_requested',
          edited_profile_text: editedProfile,
          edited_impact_text: editedImpact,
          edited_recommendations_text: editedRecommendations,
          reviewer_notes: reviewerNotes || null,
        }),
      });

      if (response.ok) {
        showToast('Changes saved successfully.', 'success');
        await fetchReport(token);
      } else {
        const errData = await response.json().catch(() => ({}));
        showToast(errData.detail || 'Failed to save changes.', 'error');
      }
    } catch (err) {
      console.error('Error saving changes:', err);
      showToast('Network error. Please try again.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleApproveReport = async () => {
    const confirmed = await confirm(
      'Are you sure you want to approve this report? Once approved, it will be available to the parent.',
      { title: 'Approve Report', confirmLabel: 'Approve' }
    );
    if (!confirmed) return;

    const token = getToken();
    if (!token) return;

    // First, save edits as an approved review
    setApproving(true);
    try {
      // Submit review with approved status
      const reviewResponse = await fetch(`${API_BASE}/reports/${reportId}/review`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          review_status: 'approved',
          edited_profile_text: editedProfile,
          edited_impact_text: editedImpact,
          edited_recommendations_text: editedRecommendations,
          reviewer_notes: reviewerNotes || null,
        }),
      });

      if (!reviewResponse.ok) {
        const errData = await reviewResponse.json().catch(() => ({}));
        showToast(errData.detail || 'Failed to approve report.', 'error');
        setApproving(false);
        return;
      }

      // Then create the final report
      const approveResponse = await fetch(`${API_BASE}/reports/${reportId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (approveResponse.ok) {
        showToast('Report approved successfully!', 'success');
        await fetchReport(token);
      } else {
        const errData = await approveResponse.json().catch(() => ({}));
        showToast(errData.detail || 'Failed to finalize report approval.', 'error');
      }
    } catch (err) {
      console.error('Error approving report:', err);
      showToast('Network error. Please try again.', 'error');
    } finally {
      setApproving(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'draft':
        return 'bg-slate-100 text-slate-700';
      case 'review':
        return 'bg-amber-100 text-amber-700';
      case 'approved':
        return 'bg-emerald-100 text-emerald-700';
      case 'rejected':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status.toLowerCase()) {
      case 'draft':
        return 'DRAFT';
      case 'review':
        return 'REVIEW';
      case 'approved':
        return 'APPROVED';
      case 'rejected':
        return 'REJECTED';
      default:
        return status.toUpperCase();
    }
  };

  const getJobStatusDisplay = (job: JobInfo | null, label: string) => {
    if (!job) return null;
    if (job.status === 'pending' || job.status === 'running') {
      return (
        <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-xl border border-blue-100">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
          <span className="text-sm font-medium text-blue-700">
            Generating... ({label})
          </span>
        </div>
      );
    }
    if (job.status === 'failed') {
      return (
        <div className="p-4 bg-red-50 rounded-xl border border-red-100">
          <p className="text-sm font-medium text-red-700">
            Generation failed: {job.error_message || 'Unknown error'}
          </p>
        </div>
      );
    }
    return null;
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

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center max-w-md">
          <svg className="w-16 h-16 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <h2 className="text-xl font-bold text-on-background mb-2">Error</h2>
          <p className="text-slate-500 mb-6">{error}</p>
          <button
            onClick={() => router.back()}
            className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-blue-600 transition-all min-h-[44px]"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!reportData) return null;

  const { report, profile_job, impact_job, recommendations_job, reviews } = reportData;
  const studentName = student ? `${student.first_name} ${student.last_name}` : 'Student';
  const isEditable = report.status !== 'approved';
  const jobsPending = hasRunningJobs(reportData);

  return (
    <div className="min-h-screen bg-background">
      <ConfirmModal {...confirmProps} />
      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 animate-in fade-in slide-in-from-top-2">
          <div
            className={`px-6 py-4 rounded-xl shadow-lg font-medium text-sm ${
              toast.type === 'success'
                ? 'bg-emerald-600 text-white'
                : 'bg-red-600 text-white'
            }`}
          >
            {toast.message}
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/psychologist/reports')}
                className="w-10 h-10 rounded-xl bg-surface hover:bg-slate-200 transition-colors flex items-center justify-center min-w-[44px] min-h-[44px]"
                aria-label="Back to reports list"
              >
                <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-lg sm:text-xl font-black text-on-background tracking-tight">
                  Report Review - {studentName}
                </h1>
                <p className="text-xs text-slate-500 font-medium">
                  Created {new Date(report.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <span
              className={`px-3 py-1.5 rounded-lg text-xs font-bold ${getStatusBadge(report.status)}`}
            >
              {getStatusLabel(report.status)}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12">
        <div className="space-y-6 sm:space-y-8">

          {/* Student Profile Section */}
          <section className="glass-card p-6 sm:p-8 rounded-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-on-background">Student Profile</h2>
            </div>

            {profile_job && (profile_job.status === 'pending' || profile_job.status === 'running') ? (
              getJobStatusDisplay(profile_job, 'profile')
            ) : profile_job && profile_job.status === 'failed' ? (
              getJobStatusDisplay(profile_job, 'profile')
            ) : isEditable ? (
              <textarea
                value={editedProfile}
                onChange={(e) => setEditedProfile(e.target.value)}
                className="w-full min-h-[200px] p-4 border border-slate-200 rounded-xl bg-white text-slate-700 leading-relaxed resize-y focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all text-sm sm:text-base"
                placeholder="Student profile text will appear here once generated..."
              />
            ) : (
              <div className="prose prose-slate max-w-none">
                <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">{editedProfile}</p>
              </div>
            )}
          </section>

          {/* Impact Assessment Section */}
          <section className="glass-card p-6 sm:p-8 rounded-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600 flex-shrink-0">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-on-background">Impact Assessment</h2>
            </div>

            {impact_job && (impact_job.status === 'pending' || impact_job.status === 'running') ? (
              getJobStatusDisplay(impact_job, 'impact')
            ) : impact_job && impact_job.status === 'failed' ? (
              getJobStatusDisplay(impact_job, 'impact')
            ) : isEditable ? (
              <textarea
                value={editedImpact}
                onChange={(e) => setEditedImpact(e.target.value)}
                className="w-full min-h-[200px] p-4 border border-slate-200 rounded-xl bg-white text-slate-700 leading-relaxed resize-y focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all text-sm sm:text-base"
                placeholder="Impact assessment text will appear here once generated..."
              />
            ) : (
              <div className="prose prose-slate max-w-none">
                <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">{editedImpact}</p>
              </div>
            )}
          </section>

          {/* Recommendations Section */}
          <section className="glass-card p-6 sm:p-8 rounded-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600 flex-shrink-0">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-on-background">Recommendations</h2>
            </div>

            {recommendations_job && (recommendations_job.status === 'pending' || recommendations_job.status === 'running') ? (
              getJobStatusDisplay(recommendations_job, 'recommendations')
            ) : recommendations_job && recommendations_job.status === 'failed' ? (
              getJobStatusDisplay(recommendations_job, 'recommendations')
            ) : isEditable ? (
              <textarea
                value={editedRecommendations}
                onChange={(e) => setEditedRecommendations(e.target.value)}
                className="w-full min-h-[200px] p-4 border border-slate-200 rounded-xl bg-white text-slate-700 leading-relaxed resize-y focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all text-sm sm:text-base"
                placeholder="Recommendations text will appear here once generated..."
              />
            ) : (
              <div className="prose prose-slate max-w-none">
                <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">{editedRecommendations}</p>
              </div>
            )}
          </section>

          {/* Reviewer Notes */}
          {isEditable && (
            <section className="glass-card p-6 sm:p-8 rounded-2xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600 flex-shrink-0">
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-on-background">Reviewer Notes</h2>
              </div>
              <textarea
                value={reviewerNotes}
                onChange={(e) => setReviewerNotes(e.target.value)}
                className="w-full min-h-[120px] p-4 border border-slate-200 rounded-xl bg-white text-slate-700 leading-relaxed resize-y focus:ring-2 focus:ring-primary focus:border-primary outline-none transition-all text-sm sm:text-base"
                placeholder="Add optional notes about your review..."
              />
            </section>
          )}

          {/* Previous Reviews */}
          {reviews.length > 0 && (
            <section className="glass-card p-6 sm:p-8 rounded-2xl">
              <h3 className="text-lg font-bold text-on-background mb-4">Review History</h3>
              <div className="space-y-3">
                {reviews.map((review) => (
                  <div key={review.id} className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                    <div className="flex items-center justify-between mb-2">
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          review.review_status === 'approved'
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {review.review_status.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(review.reviewed_at).toLocaleString()}
                      </span>
                    </div>
                    {review.reviewer_notes && (
                      <p className="text-sm text-slate-600 mt-2">{review.reviewer_notes}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-4 pb-8">
            {isEditable && !jobsPending && (
              <>
                <button
                  onClick={handleSaveChanges}
                  disabled={saving || approving}
                  className="flex-1 sm:flex-none px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] inline-flex items-center justify-center gap-2"
                >
                  {saving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </button>

                <button
                  onClick={handleApproveReport}
                  disabled={saving || approving || (!editedProfile && !editedImpact && !editedRecommendations)}
                  className="flex-1 sm:flex-none px-6 py-3 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px] inline-flex items-center justify-center gap-2"
                >
                  {approving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Approving...
                    </>
                  ) : (
                    'Approve Report'
                  )}
                </button>
              </>
            )}

            <button
              onClick={() => router.push('/psychologist/reports')}
              className="flex-1 sm:flex-none px-6 py-3 bg-surface text-slate-700 font-bold rounded-xl hover:bg-slate-200 transition-all min-h-[44px]"
            >
              Back
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
