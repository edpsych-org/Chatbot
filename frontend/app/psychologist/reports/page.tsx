'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

import { API_BASE } from '@/lib/api';

interface Report {
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
  student?: {
    first_name: string;
    last_name: string;
    grade_level?: string;
    school_name?: string;
  };
}

type FilterStatus = 'all' | 'draft' | 'review' | 'approved';

export default function PsychologistReportsListPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<{ full_name: string; email: string } | null>(null);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');

  const getToken = useCallback(() => {
    return localStorage.getItem('token');
  }, []);

  const fetchReports = useCallback(async (token: string) => {
    try {
      const response = await fetch(`${API_BASE}/reports/pending`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setReports(Array.isArray(data) ? data : []);
      } else if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        router.push('/login');
      } else {
        // Endpoint might not exist yet; try to get reports from psychologist dashboard endpoint
        setReports([]);
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
      setReports([]);
    } finally {
      setLoading(false);
    }
  }, [router]);

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

    setUser(parsedUser);
    fetchReports(token);
  }, [router, getToken, fetchReports]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
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
        return 'Draft';
      case 'review':
        return 'Review';
      case 'approved':
        return 'Approved';
      case 'rejected':
        return 'Rejected';
      default:
        return status;
    }
  };

  const filteredReports =
    filterStatus === 'all'
      ? reports
      : reports.filter((r) => r.status.toLowerCase() === filterStatus);

  const filterOptions: { value: FilterStatus; label: string; count: number }[] = [
    { value: 'all', label: 'All', count: reports.length },
    { value: 'draft', label: 'Draft', count: reports.filter((r) => r.status.toLowerCase() === 'draft').length },
    { value: 'review', label: 'Review', count: reports.filter((r) => r.status.toLowerCase() === 'review').length },
    { value: 'approved', label: 'Approved', count: reports.filter((r) => r.status.toLowerCase() === 'approved').length },
  ];

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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push('/psychologist/dashboard')}
                className="w-10 h-10 rounded-xl bg-surface hover:bg-slate-200 transition-colors flex items-center justify-center min-w-[44px] min-h-[44px]"
                aria-label="Back to dashboard"
              >
                <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-black text-on-background tracking-tight">Reports</h1>
                <p className="text-xs text-slate-500 font-medium">Review and Approve</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden md:block text-right">
                <p className="text-sm font-bold text-on-background">{user?.full_name}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-bold text-slate-600 hover:text-on-background transition-colors min-h-[44px]"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 lg:py-12">
        {/* Page Title */}
        <div className="mb-6 sm:mb-8">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-on-background mb-2">
            All Reports
          </h2>
          <p className="text-slate-500">
            {reports.length} {reports.length === 1 ? 'report' : 'reports'} total
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-2 mb-6 sm:mb-8">
          {filterOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setFilterStatus(option.value)}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all min-h-[44px] ${
                filterStatus === option.value
                  ? 'bg-primary text-white shadow-md'
                  : 'bg-surface text-slate-600 hover:bg-slate-200'
              }`}
            >
              {option.label}
              <span
                className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                  filterStatus === option.value
                    ? 'bg-white/20 text-white'
                    : 'bg-slate-200 text-slate-600'
                }`}
              >
                {option.count}
              </span>
            </button>
          ))}
        </div>

        {/* Reports Grid */}
        {filteredReports.length === 0 ? (
          <div className="glass-card p-12 rounded-2xl text-center">
            <svg className="w-20 h-20 text-slate-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-xl font-bold text-on-background mb-2">
              {filterStatus === 'all' ? 'No reports yet' : `No ${filterStatus} reports`}
            </h3>
            <p className="text-slate-500 max-w-md mx-auto">
              {filterStatus === 'all'
                ? 'Reports will appear here once assessments are completed and reports are generated.'
                : `There are no reports with "${filterStatus}" status at the moment.`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {filteredReports.map((report) => {
              const studentName = report.student
                ? `${report.student.first_name} ${report.student.last_name}`
                : `Report #${report.id.slice(0, 8)}`;

              return (
                <div
                  key={report.id}
                  className="glass-card p-6 rounded-2xl hover:shadow-xl transition-all duration-300"
                >
                  {/* Student Info */}
                  <div className="flex items-start gap-4 mb-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center text-white font-black text-xl flex-shrink-0">
                      {report.student
                        ? `${report.student.first_name[0]}${report.student.last_name[0]}`
                        : 'R'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-lg font-bold text-on-background truncate">
                        {studentName}
                      </h4>
                      {report.student?.school_name && (
                        <p className="text-sm text-slate-500 truncate">
                          {report.student.school_name}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="mb-4">
                    <span
                      className={`inline-block px-3 py-1 rounded-lg text-xs font-bold ${getStatusBadge(
                        report.status
                      )}`}
                    >
                      {getStatusLabel(report.status)}
                    </span>
                  </div>

                  {/* Details */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm">
                      <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-slate-600">
                        {new Date(report.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                      <span className="text-slate-600">
                        {[
                          report.profile_text ? 'Profile' : null,
                          report.impact_text ? 'Impact' : null,
                          report.recommendations_text ? 'Recommendations' : null,
                        ]
                          .filter(Boolean)
                          .join(', ') || 'Generating...'}
                      </span>
                    </div>
                  </div>

                  {/* Action */}
                  <div className="pt-4 border-t border-slate-200">
                    <button
                      onClick={() => router.push(`/psychologist/reports/${report.id}`)}
                      className={`w-full px-4 py-3 text-white text-sm font-bold rounded-xl transition-all min-h-[44px] ${
                        report.status.toLowerCase() === 'approved'
                          ? 'bg-emerald-600 hover:bg-emerald-700'
                          : report.status.toLowerCase() === 'review'
                          ? 'bg-amber-600 hover:bg-amber-700'
                          : 'bg-primary hover:bg-blue-600'
                      }`}
                    >
                      {report.status.toLowerCase() === 'approved'
                        ? 'View Report'
                        : report.status.toLowerCase() === 'review'
                        ? 'Review Report'
                        : 'Review Draft'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
