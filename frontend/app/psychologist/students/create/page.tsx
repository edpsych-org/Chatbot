'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { API_BASE } from '@/lib/api';

interface ParentData {
  type: string;
  full_name: string;
  email: string;
  phone: string;
  relationship: string;
  is_primary: boolean;
}

export default function CreateStudentPage() {
  const router = useRouter();

  // Student data
  const [studentData, setStudentData] = useState({
    student_first_name: '',
    student_last_name: '',
    date_of_birth: '',
    gender: '',
    grade: '',
    school_name: '',
    medical_history: '',
    notes: '',
  });

  // Parents data
  const [parents, setParents] = useState<ParentData[]>([
    {
      type: 'parent',
      full_name: '',
      email: '',
      phone: '',
      relationship: 'Mother',
      is_primary: true,
    },
  ]);

  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [createdStudentId, setCreatedStudentId] = useState('');


  const addParent = () => {
    setParents([
      ...parents,
      {
        type: 'parent',
        full_name: '',
        email: '',
        phone: '',
        relationship: 'Father',
        is_primary: false,
      },
    ]);
  };

  const removeParent = (index: number) => {
    if (parents.length > 1) {
      setParents(parents.filter((_, i) => i !== index));
    }
  };

  const updateParent = (index: number, field: keyof ParentData, value: any) => {
    const updated = [...parents];
    updated[index] = { ...updated[index], [field]: value };
    setParents(updated);
  };

  const handleSubmit = async () => {
    setError('');

    // Validation
    if (!studentData.student_first_name || !studentData.student_last_name || !studentData.date_of_birth) {
      setError('Please fill in all required student fields');
      return;
    }

    for (let i = 0; i < parents.length; i++) {
      const parent = parents[i];
      if (!parent.full_name || !parent.email || !parent.phone) {
        setError(`Please fill in all required fields for Parent/Guardian ${i + 1}`);
        return;
      }
    }

    try {
      setSubmitting(true);

      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Please log in to continue');
        return;
      }

      const response = await fetch(`${API_BASE}/psychologist/students/create-with-parents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...studentData,
          parents: parents,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Failed to create student');
        setSubmitting(false);
        return;
      }

      // Success!
      setCreatedStudentId(data.student_id);
      setSuccess(true);
      setSubmitting(false);

    } catch (err) {
      setError('Failed to create student. Please try again.');
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-green-100 mb-4">
                <svg
                  className="h-10 w-10 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Student Created Successfully!</h2>
              <p className="text-gray-600 max-w-md mx-auto">
                The parent will receive an invitation email when you assign an assessment.
              </p>
            </div>

            <div className="flex gap-4">
              <Link href="/psychologist/dashboard" className="flex-1">
                <button className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white py-3 px-6 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200">
                  Back to Dashboard
                </button>
              </Link>
              <button
                onClick={() => {
                  setSuccess(false);
                  setStudentData({
                    student_first_name: '',
                    student_last_name: '',
                    date_of_birth: '',
                    gender: '',
                    grade: '',
                    school_name: '',
                    medical_history: '',
                    notes: '',
                  });
                  setParents([
                    {
                      type: 'parent',
                      full_name: '',
                      email: '',
                      phone: '',
                      relationship: 'Mother',
                      is_primary: true,
                    },
                  ]);
                  setCurrentStep(1);
                }}
                className="flex-1 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 py-3 px-6 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
              >
                Create Another Student
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 px-4 py-6 md:py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6 md:mb-8">
          <Link href="/psychologist/dashboard" className="text-blue-600 hover:text-blue-700 font-medium mb-3 md:mb-4 inline-block text-sm md:text-base">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Create New Student</h1>
          <p className="text-sm md:text-base text-gray-600">Add student information and parent/guardian details</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center flex-1">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${currentStep >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'} font-semibold`}>
                1
              </div>
              <div className={`flex-1 h-1 mx-2 ${currentStep >= 2 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
            </div>
            <div className="flex items-center flex-1">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${currentStep >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'} font-semibold`}>
                2
              </div>
              <div className={`flex-1 h-1 mx-2 ${currentStep >= 3 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
            </div>
            <div className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${currentStep >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'} font-semibold`}>
                3
              </div>
            </div>
          </div>
          <div className="flex justify-between mt-2 text-sm font-medium">
            <span className={currentStep >= 1 ? 'text-blue-600' : 'text-gray-600'}>Student Info</span>
            <span className={currentStep >= 2 ? 'text-blue-600' : 'text-gray-600'}>Parent/Guardian</span>
            <span className={currentStep >= 3 ? 'text-blue-600' : 'text-gray-600'}>Review</span>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8">
          {/* Step 1: Student Information */}
          {currentStep === 1 && (
            <div>
              <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-6">Student Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={studentData.student_first_name}
                    onChange={(e) => setStudentData({ ...studentData, student_first_name: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    placeholder="Enter first name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={studentData.student_last_name}
                    onChange={(e) => setStudentData({ ...studentData, student_last_name: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    placeholder="Enter last name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date of Birth <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={studentData.date_of_birth}
                    onChange={(e) => setStudentData({ ...studentData, date_of_birth: e.target.value })}
                    max={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>
                  <select
                    value={studentData.gender}
                    onChange={(e) => setStudentData({ ...studentData, gender: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                  >
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                    <option value="Prefer not to say">Prefer not to say</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Grade/Year</label>
                  <input
                    type="text"
                    value={studentData.grade}
                    onChange={(e) => setStudentData({ ...studentData, grade: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    placeholder="e.g., Year 7, Grade 10"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">School Name</label>
                  <input
                    type="text"
                    value={studentData.school_name}
                    onChange={(e) => setStudentData({ ...studentData, school_name: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    placeholder="Enter school name"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Medical History</label>
                  <textarea
                    value={studentData.medical_history}
                    onChange={(e) => setStudentData({ ...studentData, medical_history: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    placeholder="Any relevant medical history or conditions"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Additional Notes</label>
                  <textarea
                    value={studentData.notes}
                    onChange={(e) => setStudentData({ ...studentData, notes: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                    placeholder="Any additional information"
                  />
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <button
                  onClick={() => setCurrentStep(2)}
                  disabled={!studentData.student_first_name || !studentData.student_last_name || !studentData.date_of_birth}
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white py-3 px-8 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next: Add Parents →
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Parent/Guardian Information */}
          {currentStep === 2 && (
            <div>
              <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-6">Parent/Guardian Information</h2>

              {parents.map((parent, index) => (
                <div key={index} className="mb-6 p-6 border-2 border-gray-200 rounded-xl relative">
                  {parents.length > 1 && (
                    <button
                      onClick={() => removeParent(index)}
                      className="absolute top-4 right-4 text-red-600 hover:text-red-700 font-semibold"
                    >
                      Remove
                    </button>
                  )}

                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Parent/Guardian {index + 1}
                    {parent.is_primary && <span className="ml-2 text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded">Primary</span>}
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Type <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={parent.type}
                        onChange={(e) => updateParent(index, 'type', e.target.value)}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                      >
                        <option value="parent">Parent</option>
                        <option value="school">School</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Full Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={parent.full_name}
                        onChange={(e) => updateParent(index, 'full_name', e.target.value)}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                        placeholder="Enter full name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="email"
                        value={parent.email}
                        onChange={(e) => updateParent(index, 'email', e.target.value)}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                        placeholder="Enter email address"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Phone <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="tel"
                        value={parent.phone}
                        onChange={(e) => updateParent(index, 'phone', e.target.value)}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                        placeholder="Enter phone number"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Relationship <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={parent.relationship}
                        onChange={(e) => updateParent(index, 'relationship', e.target.value)}
                        className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                        placeholder="e.g., Mother, Father, Guardian"
                      />
                    </div>
                    <div className="flex items-center">
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={parent.is_primary}
                          onChange={(e) => updateParent(index, 'is_primary', e.target.checked)}
                          className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm font-medium text-gray-700">Primary Contact</span>
                      </label>
                    </div>
                  </div>
                </div>
              ))}

              <button
                onClick={addParent}
                className="w-full border-2 border-dashed border-gray-300 hover:border-blue-500 text-gray-600 hover:text-blue-600 py-4 px-6 rounded-xl font-semibold transition-all duration-200"
              >
                + Add Another Parent/Guardian
              </button>

              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 py-3 px-8 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
                >
                  ← Back
                </button>
                <button
                  onClick={() => setCurrentStep(3)}
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white py-3 px-8 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
                >
                  Next: Review →
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Review and Submit */}
          {currentStep === 3 && (
            <div>
              <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-6">Review Information</h2>

              {/* Student Summary */}
              <div className="mb-6 p-6 bg-blue-50 border border-blue-200 rounded-xl">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Student Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Name:</span>
                    <p className="font-medium text-gray-900">{studentData.student_first_name} {studentData.student_last_name}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Date of Birth:</span>
                    <p className="font-medium text-gray-900">{studentData.date_of_birth}</p>
                  </div>
                  {studentData.gender && (
                    <div>
                      <span className="text-gray-600">Gender:</span>
                      <p className="font-medium text-gray-900">{studentData.gender}</p>
                    </div>
                  )}
                  {studentData.grade && (
                    <div>
                      <span className="text-gray-600">Grade:</span>
                      <p className="font-medium text-gray-900">{studentData.grade}</p>
                    </div>
                  )}
                  {studentData.school_name && (
                    <div className="col-span-2">
                      <span className="text-gray-600">School:</span>
                      <p className="font-medium text-gray-900">{studentData.school_name}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Parents Summary */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Parent/Guardian Information</h3>
                {parents.map((parent, index) => (
                  <div key={index} className="mb-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <p className="font-semibold text-gray-900 mb-2">
                      {parent.full_name} ({parent.relationship})
                      {parent.is_primary && <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">Primary</span>}
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                      <div>Email: {parent.email}</div>
                      <div>Phone: {parent.phone}</div>
                    </div>
                  </div>
                ))}
              </div>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <div className="mt-8 flex justify-between">
                <button
                  onClick={() => setCurrentStep(2)}
                  disabled={submitting}
                  className="bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 py-3 px-8 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50"
                >
                  ← Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white py-3 px-8 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? (
                    <span className="flex items-center">
                      <svg
                        className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      Creating Student...
                    </span>
                  ) : (
                    'Create Student'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
