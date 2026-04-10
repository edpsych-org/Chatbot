"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";
import ConfirmModal from "@/components/ConfirmModal";
import { useConfirm } from "@/hooks/useConfirm";

interface Assignment {
  id: string;
  student: {
    id: string;
    first_name: string;
    last_name: string;
    grade_level: string;
  } | null;
  assigned_by: {
    name: string;
    email: string;
  } | null;
  status: string;
  progress_percentage: number;
  notes: string | null;
  due_date: string | null;
  assigned_at: string;
}

interface ParentReport {
  id: string;
  student_id: string;
  status: string;
  created_at: string;
  profile_text: string | null;
  impact_text: string | null;
  recommendations_text: string | null;
  student?: {
    first_name: string;
    last_name: string;
    grade_level?: string;
    school_name?: string;
  };
}

export default function DashboardPage() {
  const router = useRouter();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [reports, setReports] = useState<ParentReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const { confirm, confirmProps } = useConfirm();

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem("access_token");
    const userData = localStorage.getItem("user");

    if (!token || !userData) {
      router.push("/login");
      return;
    }

    const parsedUser = JSON.parse(userData);

    // Redirect psychologists to their own dashboard
    if (parsedUser.role.toUpperCase() === "PSYCHOLOGIST") {
      router.push("/psychologist/dashboard");
      return;
    }

    setUser(parsedUser);

    // Fetch assignments assigned to this user
    fetchAssignments(token);
    fetchReports(token);
  }, [router]);

  const fetchAssignments = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE}/assignments/my-assignments`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAssignments(data);
      } else if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        router.push("/login");
      }
    } catch (error) {
      console.error("Error fetching assignments:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async (token: string) => {
    try {
      // Fetch reports for the parent's students from completed assignments
      // The reports/student/{id} endpoint is accessible by parents
      const assignmentsRes = await fetch(`${API_BASE}/assignments/my-assignments`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!assignmentsRes.ok) return;

      const assignmentsData: Assignment[] = await assignmentsRes.json();
      const completedAssignments = assignmentsData.filter(
        (a) => a.status === "COMPLETED" && a.student
      );

      // Get unique student IDs from completed assignments
      const studentIds = [...new Set(completedAssignments.map((a) => a.student!.id))];
      const allReports: ParentReport[] = [];

      for (const studentId of studentIds) {
        try {
          const reportsRes = await fetch(`${API_BASE}/reports/student/${studentId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (reportsRes.ok) {
            const studentReports = await reportsRes.json();
            // Only include approved reports for parent view
            const approvedReports = (Array.isArray(studentReports) ? studentReports : []).filter(
              (r: ParentReport) => r.status === "approved"
            );

            // Attach student info from assignment data
            const assignment = completedAssignments.find((a) => a.student!.id === studentId);
            for (const report of approvedReports) {
              report.student = assignment?.student
                ? {
                    first_name: assignment.student.first_name,
                    last_name: assignment.student.last_name,
                    grade_level: assignment.student.grade_level,
                  }
                : undefined;
              allReports.push(report);
            }
          }
        } catch {
          // Individual student report fetch failed, continue with others
        }
      }

      setReports(allReports);
    } catch (error) {
      console.error("Error fetching reports:", error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  const handleContinue = (assignmentId: string) => {
    router.push(`/chat/${assignmentId}`);
  };

  const handleStartAssessment = (assignmentId: string) => {
    router.push(`/chat/${assignmentId}`);
  };

  const handleStartOver = async (assignmentId: string) => {
    const confirmed = await confirm(
      "Are you sure? This will restart the assessment from the beginning.",
      { title: "Restart Assessment", confirmLabel: "Restart", variant: "danger" }
    );
    if (!confirmed) return;

    // Clear the persisted chat session for this assignment
    localStorage.removeItem(`chat_session_${assignmentId}`);

    // Navigate to the chat page — the /start endpoint will create a new session
    router.push(`/chat/${assignmentId}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ASSIGNED":
        return "bg-teal-100 text-teal-700";
      case "IN_PROGRESS":
        return "bg-amber-100 text-amber-700";
      case "COMPLETED":
        return "bg-green-100 text-green-700";
      default:
        return "bg-slate-100 text-slate-700";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "ASSIGNED":
        return "Assigned";
      case "IN_PROGRESS":
        return "In Progress";
      case "COMPLETED":
        return "Completed";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 font-medium">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <ConfirmModal {...confirmProps} />
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-black text-on-background tracking-tight">The EdPsych Practice</h1>
                <p className="text-xs text-slate-500 font-medium">Parent Dashboard</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden md:block text-right">
                <p className="text-sm font-bold text-on-background">{user?.full_name}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-bold text-slate-600 hover:text-on-background transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8 lg:py-12">
        {/* Welcome Section */}
        <div className="mb-8 lg:mb-12">
          <h2 className="text-3xl lg:text-4xl font-extrabold text-on-background mb-3">
            Welcome back, {user?.full_name?.split(' ')[0]}
          </h2>
          <p className="text-slate-500 text-lg">
            View and complete assigned assessments for your children.
          </p>
        </div>

        {/* Assignments Section */}
        <div className="mb-8">
          <h3 className="text-xl font-bold text-on-background mb-1">Assigned Assessments</h3>
          <p className="text-sm text-slate-500">
            {assignments.length} {assignments.length === 1 ? "assessment" : "assessments"} assigned
          </p>
        </div>

        {/* Assignments Grid */}
        {assignments.length === 0 ? (
          <div className="glass-card p-12 rounded-2xl text-center">
            <svg className="w-20 h-20 text-slate-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-xl font-bold text-on-background mb-2">No assessments assigned</h3>
            <p className="text-slate-500 mb-6 max-w-md mx-auto">
              You don't have any assessments assigned yet. A psychologist or administrator will assign assessments to you when needed.
            </p>
            <div className="mt-8 p-4 bg-teal-50 rounded-xl max-w-lg mx-auto">
              <p className="text-sm text-teal-900 font-medium">
                <span className="font-bold">Note:</span> Once an assessment is assigned to you by a psychologist, it will appear here and you'll be able to start it for your child.
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {assignments.map((assignment) => (
              <div
                key={assignment.id}
                className="glass-card p-6 rounded-2xl hover:shadow-xl transition-all duration-300"
              >
                {/* Student Info */}
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-500 flex items-center justify-center text-white font-black text-2xl flex-shrink-0">
                    {assignment.student?.first_name[0]}{assignment.student?.last_name[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-lg font-bold text-on-background truncate">
                      {assignment.student?.first_name} {assignment.student?.last_name}
                    </h4>
                    <p className="text-sm text-slate-500">
                      Grade {assignment.student?.grade_level}
                    </p>
                  </div>
                </div>

                {/* Status Badge & Progress */}
                <div className="mb-4 flex items-center gap-3">
                  <span className={`inline-block px-3 py-1 rounded-lg text-xs font-bold ${getStatusColor(assignment.status)}`}>
                    {getStatusText(assignment.status)}
                  </span>
                  {assignment.status === "IN_PROGRESS" && (
                    <span className="text-sm font-semibold text-amber-700">
                      {assignment.progress_percentage ?? 0}% complete
                    </span>
                  )}
                </div>

                {/* Progress Bar for IN_PROGRESS */}
                {assignment.status === "IN_PROGRESS" && (
                  <div className="mb-4">
                    <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-amber-400 to-amber-500 rounded-full transition-all duration-500"
                        style={{ width: `${assignment.progress_percentage ?? 0}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Assignment Details */}
                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm">
                    <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span className="text-slate-600 truncate">Assigned by: {assignment.assigned_by?.name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span className="text-slate-600">
                      Assigned {new Date(assignment.assigned_at).toLocaleDateString()}
                    </span>
                  </div>
                  {assignment.due_date && (
                    <div className="flex items-center gap-2 text-sm">
                      <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-slate-600">
                        Due {new Date(assignment.due_date).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                {/* Notes */}
                {assignment.notes && (
                  <div className="mb-4 p-3 bg-teal-50 rounded-lg">
                    <p className="text-xs font-bold text-teal-900 mb-1">Notes:</p>
                    <p className="text-sm text-teal-800">{assignment.notes}</p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2 pt-4 border-t border-slate-200">
                  {assignment.status === "IN_PROGRESS" && (
                    <>
                      <button
                        onClick={() => handleContinue(assignment.id)}
                        className="flex-1 px-4 py-2.5 bg-primary text-white text-sm font-bold rounded-lg hover:bg-teal-600 transition-all"
                      >
                        Continue for {assignment.student?.first_name} ({assignment.progress_percentage ?? 0}%)
                      </button>
                      <button
                        onClick={() => handleStartOver(assignment.id)}
                        className="px-4 py-2.5 bg-white text-slate-600 text-sm font-bold rounded-lg border border-slate-300 hover:bg-slate-50 hover:text-red-600 hover:border-red-300 transition-all"
                        title="Start the assessment over from the beginning"
                      >
                        Start Over
                      </button>
                    </>
                  )}
                  {assignment.status === "ASSIGNED" && (
                    <button
                      onClick={() => handleStartAssessment(assignment.id)}
                      className="flex-1 px-4 py-2.5 bg-primary text-white text-sm font-bold rounded-lg hover:bg-teal-600 transition-all"
                    >
                      Start Assessment
                    </button>
                  )}
                  {assignment.status === "COMPLETED" && (
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-green-50 text-green-700 text-sm font-bold rounded-lg border border-green-200">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                          </svg>
                          Assessment Complete
                        </span>
                        <button
                          onClick={() => router.push(`/parent/reports/${assignment.id}`)}
                          className="px-4 py-2.5 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition-all"
                        >
                          View Report
                        </button>
                      </div>
                      <p className="text-xs text-slate-400">This assessment has been submitted and cannot be retaken.</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Reports Section */}
        <div className="mt-12 lg:mt-16">
          <div className="mb-8">
            <h3 className="text-xl font-bold text-on-background mb-1">Assessment Reports</h3>
            <p className="text-sm text-slate-500">
              {reports.length > 0
                ? `${reports.length} approved ${reports.length === 1 ? "report" : "reports"} available`
                : "Approved reports will appear here"}
            </p>
          </div>

          {reports.length === 0 ? (
            <div className="glass-card p-8 sm:p-12 rounded-2xl text-center">
              <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-bold text-on-background mb-2">No reports available yet</h3>
              <p className="text-slate-500 max-w-md mx-auto text-sm">
                Once an assessment is completed and the psychologist has reviewed and approved the report, it will appear here for you to view.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {reports.map((report) => {
                const studentName = report.student
                  ? `${report.student.first_name} ${report.student.last_name}`
                  : "Student";

                return (
                  <div
                    key={report.id}
                    className="glass-card p-6 rounded-2xl hover:shadow-xl transition-all duration-300"
                  >
                    {/* Student Info */}
                    <div className="flex items-start gap-4 mb-4">
                      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white font-black text-xl flex-shrink-0">
                        {report.student
                          ? `${report.student.first_name[0]}${report.student.last_name[0]}`
                          : "R"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-lg font-bold text-on-background truncate">
                          {studentName}
                        </h4>
                        {report.student?.grade_level && (
                          <p className="text-sm text-slate-500">
                            Grade {report.student.grade_level}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Status */}
                    <div className="mb-4">
                      <span className="inline-block px-3 py-1 rounded-lg text-xs font-bold bg-emerald-100 text-emerald-700">
                        Approved
                      </span>
                    </div>

                    {/* Date */}
                    <div className="flex items-center gap-2 text-sm mb-4">
                      <svg className="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-slate-600">
                        {new Date(report.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    {/* Action */}
                    <div className="pt-4 border-t border-slate-200">
                      <button
                        onClick={() => router.push(`/parent/reports/${report.id}`)}
                        className="w-full px-4 py-3 bg-emerald-600 text-white text-sm font-bold rounded-xl hover:bg-emerald-700 transition-all min-h-[44px]"
                      >
                        View Report
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
