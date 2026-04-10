"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { API_BASE } from "@/lib/api";

interface Student {
  id: number;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  grade_level: string;
  school_name: string;
  created_at: string;
}

interface Assessment {
  id: number;
  session_token: string;
  status: string;
  progress_percentage: number;
  created_at: string;
  completed_at: string | null;
}

export default function StudentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const studentId = params.id as string;

  const [student, setStudent] = useState<Student | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    fetchStudentData(token);
  }, [studentId, router]);

  const fetchStudentData = async (token: string) => {
    try {
      // Fetch student details
      const studentResponse = await fetch(
        `${API_BASE}/students/${studentId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (studentResponse.ok) {
        const studentData = await studentResponse.json();
        setStudent(studentData);
      }

      // Fetch student assessments
      const assessmentsResponse = await fetch(
        `${API_BASE}/chatbot/sessions/${studentId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (assessmentsResponse.ok) {
        const assessmentsData = await assessmentsResponse.json();
        setAssessments(assessmentsData);
      }
    } catch (error) {
      console.error("Error fetching student data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAssessment = async () => {
    // Redirect to the intermediate assessment page which will handle session creation
    router.push(`/student/${studentId}/assessment`);
  };

  const calculateAge = (dateOfBirth: string) => {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
      case "IN_PROGRESS":
        return "bg-teal-100 text-teal-700 border-teal-200";
      case "DRAFT":
        return "bg-slate-100 text-slate-700 border-slate-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 font-medium">Loading student data...</p>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-500 font-medium">Student not found</p>
          <button
            onClick={() => router.push("/dashboard")}
            className="mt-4 px-6 py-2 bg-primary text-white font-bold rounded-xl"
          >
            Back to Dashboard
          </button>
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
                onClick={() => router.push("/dashboard")}
                className="w-10 h-10 rounded-xl bg-surface hover:bg-slate-200 transition-colors flex items-center justify-center"
              >
                <svg className="w-5 h-5 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-black text-on-background tracking-tight">The EdPsych Practice</h1>
                  <p className="text-xs text-slate-500 font-medium">Student Profile</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8 lg:py-12">
        {/* Student Profile Card */}
        <div className="glass-card p-8 rounded-3xl mb-8">
          <div className="flex flex-col lg:flex-row items-start lg:items-center gap-6">
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-teal-500 to-teal-500 flex items-center justify-center text-white font-black text-4xl flex-shrink-0">
              {student.first_name[0]}{student.last_name[0]}
            </div>
            <div className="flex-1">
              <h2 className="text-3xl font-extrabold text-on-background mb-2">
                {student.first_name} {student.last_name}
              </h2>
              <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Age {calculateAge(student.date_of_birth)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  <span>Grade {student.grade_level}</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                  </svg>
                  <span>{student.school_name}</span>
                </div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => router.push(`/student/${studentId}/workspace`)}
                className="px-6 py-4 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold rounded-xl shadow-lg hover:shadow-xl hover:from-emerald-600 hover:to-teal-600 transition-all flex items-center gap-2"
              >
                <span role="img" aria-label="clipboard">📋</span>
                Open Reports Workspace
              </button>
              <button
                onClick={handleStartAssessment}
                className="px-8 py-4 bg-on-background text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-all flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                New Assessment
              </button>
            </div>
          </div>
        </div>

        {/* Assessments Section */}
        <div>
          <h3 className="text-2xl font-bold text-on-background mb-6">Assessment History</h3>

          {assessments.length === 0 ? (
            <div className="glass-card p-12 rounded-2xl text-center">
              <svg className="w-16 h-16 text-slate-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentCloud">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h4 className="text-lg font-bold text-on-background mb-2">No assessments yet</h4>
              <p className="text-slate-500 mb-6">
                Start the first assessment to begin tracking this student's educational progress.
              </p>
              <button
                onClick={handleStartAssessment}
                className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:bg-teal-600 transition-all inline-flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Start First Assessment
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {assessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className="glass-card p-6 rounded-2xl hover:shadow-lg transition-all cursor-pointer"
                  onClick={() => {
                    if (assessment.status !== "COMPLETED") {
                      router.push(`/student/${studentId}/assessment/${assessment.session_token}`);
                    }
                  }}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="text-lg font-bold text-on-background">
                          Assessment #{assessment.id}
                        </h4>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(assessment.status)}`}>
                          {assessment.status.replace("_", " ")}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">
                        Started: {new Date(assessment.created_at).toLocaleString()}
                      </p>
                      {assessment.completed_at && (
                        <p className="text-sm text-slate-600">
                          Completed: {new Date(assessment.completed_at).toLocaleString()}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-6">
                      {/* Progress Circle */}
                      <div className="relative w-20 h-20">
                        <svg className="w-20 h-20 transform -rotate-90">
                          <circle
                            cx="40"
                            cy="40"
                            r="32"
                            stroke="currentColor"
                            strokeWidth="6"
                            fill="none"
                            className="text-slate-200"
                          />
                          <circle
                            cx="40"
                            cy="40"
                            r="32"
                            stroke="currentColor"
                            strokeWidth="6"
                            fill="none"
                            strokeDasharray={`${2 * Math.PI * 32}`}
                            strokeDashoffset={`${2 * Math.PI * 32 * (1 - assessment.progress_percentage / 100)}`}
                            className="text-primary transition-all duration-500"
                            strokeLinecap="round"
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-sm font-bold text-on-background">
                            {Math.round(assessment.progress_percentage)}%
                          </span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                        {assessment.status === "COMPLETED" ? (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/student/${studentId}/reports`);
                            }}
                            className="px-4 py-2 bg-emerald-500 text-white text-sm font-bold rounded-lg hover:bg-emerald-600 transition-all"
                          >
                            View Report
                          </button>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              router.push(`/student/${studentId}/assessment/${assessment.session_token}`);
                            }}
                            className="px-4 py-2 bg-primary text-white text-sm font-bold rounded-lg hover:bg-teal-600 transition-all"
                          >
                            Continue
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
