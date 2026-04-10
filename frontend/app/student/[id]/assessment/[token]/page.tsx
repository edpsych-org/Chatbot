"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { API_BASE } from "@/lib/api";

interface Question {
  id: number;
  section: string;
  question_text: string;
  question_type: string;
  options: string[] | { choices?: string[]; [key: string]: any } | null;
  min_value: number | null;
  max_value: number | null;
  min_label: string | null;
  max_label: string | null;
}

interface SessionProgress {
  session_id: number;
  student_id: number;
  status: string;
  total_questions: number;
  answered_questions: number;
  progress_percentage: number;
  current_question: Question | null;
  next_question: Question | null;
}

export default function AssessmentPage() {
  const router = useRouter();
  const params = useParams();
  const studentId = params.id as string;
  const sessionToken = params.token as string;

  const [progress, setProgress] = useState<SessionProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [answer, setAnswer] = useState<string>("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    // Redirect to hybrid chat instead of using traditional assessment
    redirectToHybridChat(token);
  }, [sessionToken, router, studentId]);

  const redirectToHybridChat = async (token: string) => {
    try {
      // Get the user's assignments to find the assignment ID
      const response = await fetch(
        `${API_BASE}/assignments/my-assignments`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const assignments = await response.json();
        if (assignments && assignments.length > 0) {
          // Find assignment for this student or use the first one
          const matchingAssignment = assignments.find(
            (a: any) => a.student?.id === studentId
          ) || assignments[0];

          const assignmentId = matchingAssignment.id;
          router.push(`/chat/${assignmentId}`);
          return;
        }
      }

      // Fallback: if no assignments found, still try to fetch progress for old system
      fetchProgress(token);
    } catch (error) {
      console.error("Error redirecting to hybrid chat:", error);
      // Fallback to old system on error
      fetchProgress(token);
    }
  };

  const fetchProgress = async (token: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/chatbot/progress/${sessionToken}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.ok) {
        const data = await response.json();
        console.log("=== ASSESSMENT PROGRESS DEBUG ===");
        console.log("Session Token:", sessionToken);
        console.log("Total Questions:", data.total_questions);
        console.log("Answered Questions:", data.answered_questions);
        console.log("Progress Percentage:", data.progress_percentage);
        console.log("Current Question Number:", data.answered_questions + 1);
        console.log("Next Question:", data.next_question);
        console.log("Session Status:", data.session?.status);
        console.log("================================");
        setProgress(data);

        // Check if assessment is completed
        if (data.session?.status === "COMPLETED" || !data.next_question) {
          router.push(`/student/${studentId}/reports`);
        }
      } else if (response.status === 401) {
        router.push("/login");
      }
    } catch (error) {
      console.error("Error fetching progress:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!answer.trim()) {
      alert("Please provide an answer before continuing.");
      return;
    }

    setSubmitting(true);

    try {
      const token = localStorage.getItem("access_token");
      const currentQuestion = progress?.next_question;

      if (!currentQuestion) {
        return;
      }

      const response = await fetch(`${API_BASE}/chatbot/answer`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_token: sessionToken,
          question_id: currentQuestion.id,
          answer_text: answer,
          answer_data: currentQuestion.question_type === "SCALE" ? { value: parseInt(answer) } : {},
        }),
      });

      if (response.ok) {
        const data = await response.json();

        // Check if completed
        if (data.status === "COMPLETED") {
          router.push(`/student/${studentId}/reports`);
        } else {
          // Refresh progress
          setAnswer("");
          await fetchProgress(token!);
        }
      } else {
        alert("Failed to submit answer. Please try again.");
      }
    } catch (error) {
      console.error("Error submitting answer:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500 font-medium">Loading assessment...</p>
        </div>
      </div>
    );
  }

  if (!progress || !progress.next_question) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-500 font-medium">No questions available</p>
          <button
            onClick={() => router.push(`/student/${studentId}`)}
            className="mt-4 px-6 py-2 bg-primary text-white font-bold rounded-xl"
          >
            Back to Student
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = progress.next_question;
  const questionNumber = progress.answered_questions + 1;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-black text-on-background">Assessment in Progress</h1>
                <p className="text-xs text-slate-500">
                  Question {questionNumber} of {progress.total_questions}
                </p>
              </div>
            </div>
            <button
              onClick={() => router.push(`/student/${studentId}`)}
              className="text-sm font-bold text-slate-600 hover:text-on-background transition-colors"
            >
              Save & Exit
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-slate-600">
                {Math.round(progress.progress_percentage)}% Complete
              </span>
              <span className="text-xs text-slate-500">
                {progress.answered_questions} / {progress.total_questions} answered
              </span>
            </div>
            <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-teal-500 to-teal-500 transition-all duration-500"
                style={{ width: `${progress.progress_percentage}%` }}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="glass-card p-8 lg:p-12 rounded-3xl">
          {/* Section Badge */}
          <div className="mb-6">
            <span className="inline-block px-4 py-2 bg-teal-100 text-teal-700 text-xs font-bold uppercase tracking-wider rounded-lg border border-teal-200">
              {currentQuestion.section}
            </span>
          </div>

          {/* Question */}
          <h2 className="text-2xl lg:text-3xl font-extrabold text-on-background mb-8 leading-relaxed">
            {currentQuestion.question_text}
          </h2>

          {/* Answer Input */}
          <div className="mb-8">
            {currentQuestion.question_type === "SCALE" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center px-2">
                  <span className="text-sm font-medium text-slate-600">
                    {currentQuestion.min_label}
                  </span>
                  <span className="text-sm font-medium text-slate-600">
                    {currentQuestion.max_label}
                  </span>
                </div>
                <div className="flex gap-3 justify-center">
                  {Array.from(
                    { length: (currentQuestion.max_value || 5) - (currentQuestion.min_value || 1) + 1 },
                    (_, i) => (currentQuestion.min_value || 1) + i
                  ).map((value) => (
                    <button
                      key={value}
                      onClick={() => setAnswer(value.toString())}
                      className={`w-14 h-14 rounded-xl font-bold text-lg transition-all ${
                        answer === value.toString()
                          ? "bg-primary text-white shadow-lg scale-110"
                          : "bg-surface text-slate-700 hover:bg-slate-200 border border-slate-300"
                      }`}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {currentQuestion.question_type === "YES_NO" && (
              <div className="flex gap-4">
                <button
                  onClick={() => setAnswer("Yes")}
                  className={`flex-1 py-4 rounded-xl font-bold text-lg transition-all ${
                    answer === "Yes"
                      ? "bg-primary text-white shadow-lg"
                      : "bg-surface text-slate-700 hover:bg-slate-200 border border-slate-300"
                  }`}
                >
                  Yes
                </button>
                <button
                  onClick={() => setAnswer("No")}
                  className={`flex-1 py-4 rounded-xl font-bold text-lg transition-all ${
                    answer === "No"
                      ? "bg-primary text-white shadow-lg"
                      : "bg-surface text-slate-700 hover:bg-slate-200 border border-slate-300"
                  }`}
                >
                  No
                </button>
              </div>
            )}

            {currentQuestion.question_type === "MULTIPLE_CHOICE" && currentQuestion.options && (
              <div className="space-y-3">
                {(Array.isArray(currentQuestion.options)
                  ? currentQuestion.options
                  : currentQuestion.options.choices || []
                ).map((option: any, index: number) => {
                  const optionValue = typeof option === 'string' ? option : (option.value || option.label || String(option));
                  const optionLabel = typeof option === 'string' ? option : (option.label || option.value || String(option));

                  return (
                    <button
                      key={index}
                      onClick={() => setAnswer(optionValue)}
                      className={`w-full p-4 rounded-xl text-left font-medium transition-all ${
                        answer === optionValue
                          ? "bg-primary text-white shadow-lg"
                          : "bg-surface text-slate-700 hover:bg-slate-200 border border-slate-300"
                      }`}
                    >
                      {optionLabel}
                    </button>
                  );
                })}
              </div>
            )}

            {currentQuestion.question_type === "TEXT" && (
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="w-full px-6 py-4 bg-surface border border-slate-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-on-surface outline-none resize-none"
                rows={6}
                placeholder="Type your answer here..."
              />
            )}
          </div>

          {/* Navigation Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => router.push(`/student/${studentId}`)}
              className="px-6 py-4 border-2 border-slate-300 text-slate-700 font-bold rounded-xl hover:border-slate-400 transition-all"
            >
              Save & Exit
            </button>
            <button
              onClick={handleSubmitAnswer}
              disabled={!answer.trim() || submitting}
              className="flex-1 px-6 py-4 bg-on-background text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <span>
                    {questionNumber === progress.total_questions ? "Complete Assessment" : "Next Question"}
                  </span>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Help Card */}
        <div className="mt-8 p-6 bg-teal-50 border border-teal-200 rounded-2xl">
          <div className="flex gap-4">
            <svg className="w-6 h-6 text-teal-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 className="font-bold text-teal-900 mb-1">Assessment Tips</h4>
              <p className="text-sm text-teal-700 leading-relaxed">
                Answer honestly and thoughtfully. There are no right or wrong answers. Your responses help us understand your child's educational needs better. You can save and exit at any time to continue later.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
