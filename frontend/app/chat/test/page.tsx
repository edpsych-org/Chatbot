'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';

import { API_BASE } from '@/lib/api';

interface Assignment {
  id: string;
  student_id: string;
  assigned_to_user_id: string;
  status: string;
  assigned_at: string;
  student?: {
    first_name: string;
    last_name: string;
  };
}

export default function ChatTestPage() {
  const router = useRouter();
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [testAssignmentId, setTestAssignmentId] = useState('');
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Please login first');
        return;
      }

      const response = await axios.get(`${API_BASE}/assignments/my-assignments`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setAssignments(response.data || []);
    } catch (error: any) {
      console.error('Failed to load assignments:', error);
    } finally {
      setLoading(false);
    }
  };

  const startChat = (assignmentId: string) => {
    router.push(`/chat/${assignmentId}`);
  };

  const startTestChat = () => {
    if (testAssignmentId.trim()) {
      router.push(`/chat/${testAssignmentId}`);
    } else {
      alert('Please enter an assignment ID');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Hybrid Chat Test Page</h1>
            <p className="text-gray-600">
              Welcome, <span className="font-semibold text-green-600">{user?.full_name || 'User'}</span>
            </p>
          </div>

          {/* Test Direct Access */}
          <div className="mb-8 p-6 bg-yellow-50 border-2 border-yellow-300 rounded-xl">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Test (Direct Access)</h2>
            <p className="text-sm text-gray-600 mb-4">
              Enter any assignment ID to test the chat directly:
            </p>
            <div className="flex gap-3">
              <input
                type="text"
                value={testAssignmentId}
                onChange={(e) => setTestAssignmentId(e.target.value)}
                placeholder="Paste assignment ID here..."
                className="flex-1 border-2 border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:border-yellow-500"
              />
              <button
                onClick={startTestChat}
                className="bg-yellow-500 hover:bg-yellow-600 text-white px-6 py-2 rounded-lg font-medium transition-colors"
              >
                Start Test Chat
              </button>
            </div>
          </div>

          {/* Your Assignments */}
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Assignments</h2>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-green-500"></div>
                <p className="mt-4 text-gray-600">Loading assignments...</p>
              </div>
            ) : assignments.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-xl">
                <p className="text-xl text-gray-600 mb-2">No assignments found</p>
                <p className="text-sm text-gray-500">
                  You don't have any active assessments assigned yet.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {assignments.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="border-2 border-gray-200 rounded-xl p-5 hover:border-green-500 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          Assessment for{' '}
                          {assignment.student?.first_name} {assignment.student?.last_name || 'Student'}
                        </h3>
                        <p className="text-sm text-gray-600">
                          Status:{' '}
                          <span
                            className={`font-medium ${
                              assignment.status === 'ASSIGNED'
                                ? 'text-yellow-600'
                                : assignment.status === 'IN_PROGRESS'
                                ? 'text-teal-600'
                                : 'text-green-600'
                            }`}
                          >
                            {assignment.status}
                          </span>
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Assigned: {new Date(assignment.assigned_at).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-gray-400 font-mono mt-1">ID: {assignment.id}</p>
                      </div>
                      <button
                        onClick={() => startChat(assignment.id)}
                        className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-xl font-medium shadow-md hover:shadow-lg transition-all duration-200"
                      >
                        {assignment.status === 'IN_PROGRESS' ? 'Continue Chat' : 'Start Assessment'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info Section */}
          <div className="mt-8 p-6 bg-teal-50 border-2 border-teal-300 rounded-xl">
            <h3 className="text-lg font-bold text-gray-900 mb-2">How it works:</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <span className="text-green-500 mr-2">1.</span>
                <span>Click "Start Assessment" to begin the hybrid chat</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2">2.</span>
                <span>Answer questions using quick-reply buttons (MCQ) OR type your own answer</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2">3.</span>
                <span>You will be guided through the assessment step by step</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-500 mr-2">4.</span>
                <span>Your progress is saved automatically</span>
              </li>
            </ul>
          </div>

          {/* Navigation */}
          <div className="mt-6 text-center">
            <button
              onClick={() => router.push('/parent/dashboard')}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
