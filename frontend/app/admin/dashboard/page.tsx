"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";
import DataExplorer from "@/src/components/admin/DataExplorer";

interface User {
  id: string;
  email: string;
  role: string;
  full_name: string;
  phone: string | null;
  organization: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

interface SystemStats {
  total_users: number;
  total_students: number;
  total_assessments: number;
  total_reports: number;
  active_sessions: number;
  users_by_role: {
    PARENT: number;
    PSYCHOLOGIST: number;
    SCHOOL: number;
    ADMIN: number;
  };
}

/* ─── Reusable Modal Shell ─── */
function ModalOverlay({
  open,
  onClose,
  children,
  maxW = "max-w-md",
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  maxW?: string;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className={`bg-white rounded-2xl shadow-2xl ${maxW} w-full max-h-[85vh] overflow-y-auto animate-scale-in`}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  );
}

/* ─── Dialog (confirm / alert) ─── */
function Dialog({
  open,
  title,
  message,
  variant = "info",
  confirmLabel = "OK",
  cancelLabel,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  message: string;
  variant?: "info" | "warning" | "danger" | "success";
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel?: () => void;
}) {
  const btnColor = {
    info: "bg-primary hover:bg-teal-700",
    warning: "bg-amber-500 hover:bg-amber-600",
    danger: "bg-red-500 hover:bg-red-600",
    success: "bg-emerald-500 hover:bg-emerald-600",
  }[variant];
  const iconColor = {
    info: "text-primary bg-teal-50",
    warning: "text-amber-500 bg-amber-50",
    danger: "text-red-500 bg-red-50",
    success: "text-emerald-500 bg-emerald-50",
  }[variant];
  const icons = {
    info: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />,
    warning: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />,
    danger: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />,
    success: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />,
  };

  return (
    <ModalOverlay open={open} onClose={onCancel || onConfirm}>
      <div className="p-6">
        <div className="flex items-start gap-4 mb-5">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconColor}`}>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">{icons[variant]}</svg>
          </div>
          <div>
            <h3 className="text-base font-semibold text-on-background">{title}</h3>
            <p className="text-sm text-[#737373] mt-1 whitespace-pre-line leading-relaxed">{message}</p>
          </div>
        </div>
        <div className="flex gap-3 justify-end">
          {cancelLabel && onCancel && (
            <button onClick={onCancel} className="px-4 py-2 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
              {cancelLabel}
            </button>
          )}
          <button onClick={onConfirm} className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors ${btnColor}`}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </ModalOverlay>
  );
}

/* ─── Stat Card ─── */
function StatCard({
  label,
  value,
  icon,
  color,
  onClick,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="group bg-white backdrop-blur-sm rounded-2xl border border-[#dedede] p-5 text-left hover:bg-[#f4f4f4] hover:border-[#cccccc] transition-all duration-200 w-full"
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
          {icon}
        </div>
        <svg className="w-4 h-4 text-slate-600 group-hover:text-[#737373] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
      <p className="font-serif text-3xl font-bold text-[#333] tracking-tight">{value}</p>
      <p className="text-xs font-medium text-[#737373] mt-0.5 uppercase tracking-wide">{label}</p>
    </button>
  );
}

/* ─── Role Badge ─── */
function RoleBadge({ role }: { role: string }) {
  const styles: Record<string, string> = {
    ADMIN: "bg-[#fdecec] text-[#e61844]",
    PSYCHOLOGIST: "bg-teal-100 text-teal-700",
    SCHOOL: "bg-sky-100 text-sky-700",
    PARENT: "bg-emerald-100 text-emerald-700",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[0.6875rem] font-semibold tracking-wide ${styles[role] || "bg-slate-100 text-slate-600"}`}>
      {role}
    </span>
  );
}

/* ─── Main Dashboard ─── */
export default function AdminDashboard() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [filterRole, setFilterRole] = useState<string>("all");
  const [showAddUser, setShowAddUser] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [createForm, setCreateForm] = useState({ full_name: "", email: "", password: "", role: "PSYCHOLOGIST", phone: "", organization: "" });
  const [createError, setCreateError] = useState("");
  const [creating, setCreating] = useState(false);
  const [editForm, setEditForm] = useState({ full_name: "", email: "", phone: "", organization: "", role: "" });
  const [editError, setEditError] = useState("");
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState<string | null>(null);
  const [statPopup, setStatPopup] = useState<{ open: boolean; title: string; items: { id: string; label: string; sub?: string }[]; loading: boolean }>({ open: false, title: "", items: [], loading: false });
  const [dialog, setDialog] = useState<{ open: boolean; title: string; message: string; variant: "info" | "warning" | "danger" | "success"; confirmLabel: string; cancelLabel?: string; onConfirm: () => void; onCancel?: () => void }>({ open: false, title: "", message: "", variant: "info", confirmLabel: "OK", onConfirm: () => {} });
  const [activeTab, setActiveTab] = useState<"users" | "students" | "assignments" | "explorer">("users");

  /* ─── Students tab state ─── */
  const [adminStudents, setAdminStudents] = useState<any[]>([]);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [showCreateStudent, setShowCreateStudent] = useState(false);
  const [studentForm, setStudentForm] = useState({
    student_first_name: "", student_last_name: "", date_of_birth: "", gender: "", grade: "", school_name: "",
    parents: [{ type: "parent", full_name: "", email: "", phone: "", relationship: "Mother", is_primary: true }],
  });
  const [studentFormError, setStudentFormError] = useState("");
  const [creatingStudent, setCreatingStudent] = useState(false);

  /* ─── Assignments tab state ─── */
  const [adminAssignments, setAdminAssignments] = useState<any[]>([]);
  const [assignmentsLoading, setAssignmentsLoading] = useState(false);
  const [showAssignForm, setShowAssignForm] = useState(false);
  const [assignStudents, setAssignStudents] = useState<any[]>([]);
  const [assignForm, setAssignForm] = useState({ student_id: "", parent_id: "", notes: "" });
  const [assignFormError, setAssignFormError] = useState("");
  const [assigning, setAssigning] = useState(false);
  const [selectedStudentGuardians, setSelectedStudentGuardians] = useState<any[]>([]);

  const showAlert = (title: string, message: string, variant: "info" | "warning" | "danger" | "success" = "info") => {
    setDialog({ open: true, title, message, variant, confirmLabel: "OK", onConfirm: () => setDialog((d) => ({ ...d, open: false })) });
  };

  const showConfirm = (title: string, message: string, variant: "warning" | "danger", confirmLabel: string, onConfirm: () => void) => {
    setDialog({ open: true, title, message, variant, confirmLabel, cancelLabel: "Cancel", onConfirm: () => { setDialog((d) => ({ ...d, open: false })); onConfirm(); }, onCancel: () => setDialog((d) => ({ ...d, open: false })) });
  };

  /* ─── Data fetching ─── */
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const userData = localStorage.getItem("user");
    if (!token || !userData) { router.push("/login"); return; }
    const parsedUser = JSON.parse(userData);
    if (parsedUser.role !== "ADMIN") { router.push("/dashboard"); return; }
    setUser(parsedUser);
    fetchAdminData(token);
  }, [router]);

  const fetchAdminData = async (token: string) => {
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [usersRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/admin/users`, { headers }),
        fetch(`${API_BASE}/admin/stats`, { headers }).catch(() => null),
      ]);
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setUsers(usersData);
        const fallbackRoles = {
          PARENT: usersData.filter((u: User) => u.role === "PARENT").length,
          PSYCHOLOGIST: usersData.filter((u: User) => u.role === "PSYCHOLOGIST").length,
          SCHOOL: usersData.filter((u: User) => u.role === "SCHOOL").length,
          ADMIN: usersData.filter((u: User) => u.role === "ADMIN").length,
        };
        if (statsRes?.ok) {
          const s = await statsRes.json();
          setStats({ total_users: s.total_users ?? usersData.length, total_students: s.total_students ?? 0, total_assessments: s.total_assessments ?? 0, total_reports: s.total_reports ?? 0, active_sessions: 0, users_by_role: s.users_by_role ?? fallbackRoles });
        } else {
          setStats({ total_users: usersData.length, total_students: 0, total_assessments: 0, total_reports: 0, active_sessions: 0, users_by_role: fallbackRoles });
        }
      }
    } catch (error) {
      console.error("Error fetching admin data:", error);
    } finally {
      setLoading(false);
    }
  };

  /* ─── Students data ─── */
  const fetchAdminStudents = async () => {
    setStudentsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/admin/students/all-with-details`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setAdminStudents(data.students || []); }
    } catch (e) { console.error("Error fetching students:", e); }
    finally { setStudentsLoading(false); }
  };

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setStudentFormError("");
    setCreatingStudent(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/admin/students/create-with-parents`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(studentForm),
      });
      if (res.ok) {
        setShowCreateStudent(false);
        setStudentForm({ student_first_name: "", student_last_name: "", date_of_birth: "", gender: "", grade: "", school_name: "", parents: [{ type: "parent", full_name: "", email: "", phone: "", relationship: "Mother", is_primary: true }] });
        fetchAdminStudents();
        showAlert("Success", "Student created successfully!", "success");
      } else { const d = await res.json().catch(() => null); setStudentFormError(d?.detail || "Failed to create student"); }
    } catch { setStudentFormError("Network error."); }
    finally { setCreatingStudent(false); }
  };

  /* ─── Assignments data ─── */
  const fetchAdminAssignments = async () => {
    setAssignmentsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/admin/assignments/all`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setAdminAssignments(data || []); }
    } catch (e) { console.error("Error fetching assignments:", e); }
    finally { setAssignmentsLoading(false); }
  };

  const fetchStudentsForAssign = async () => {
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/admin/students/all-with-details`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const data = await res.json(); setAssignStudents(data.students || []); }
    } catch {}
  };

  const handleStudentSelectForAssign = (studentId: string) => {
    setAssignForm({ ...assignForm, student_id: studentId, parent_id: "" });
    const student = assignStudents.find((s: any) => s.id === studentId);
    setSelectedStudentGuardians(student?.guardians || []);
  };

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    setAssignFormError("");
    if (!assignForm.student_id || !assignForm.parent_id) { setAssignFormError("Select both student and parent"); return; }
    setAssigning(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${API_BASE}/admin/assignments/assign`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(assignForm),
      });
      if (res.ok) {
        setShowAssignForm(false);
        setAssignForm({ student_id: "", parent_id: "", notes: "" });
        fetchAdminAssignments();
        showAlert("Success", "Assessment assigned and magic link sent!", "success");
      } else { const d = await res.json().catch(() => null); setAssignFormError(d?.detail || "Failed to assign"); }
    } catch { setAssignFormError("Network error."); }
    finally { setAssigning(false); }
  };

  const handleResendInvite = async (assignmentId: string) => {
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(`${API_BASE}/admin/assignments/${assignmentId}/resend-link`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const link = data.magic_link || "";
        try { await navigator.clipboard.writeText(link); } catch {}
        showAlert("Magic Link Ready", `Copied to clipboard and emailed to ${data.sent_to}.\n\n${link}`, "success");
      } else showAlert("Error", "Failed to resend invite", "danger");
    } catch { showAlert("Error", "Network error", "danger"); }
  };

  const handleCancelAssignment = (assignmentId: string) => {
    showConfirm("Cancel Assignment", "Are you sure you want to cancel this assignment?", "danger", "Cancel Assignment", async () => {
      const token = localStorage.getItem("access_token");
      try {
        const res = await fetch(`${API_BASE}/admin/assignments/${assignmentId}/cancel`, {
          method: "PATCH", headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) { fetchAdminAssignments(); showAlert("Cancelled", "Assignment cancelled", "info"); }
        else showAlert("Error", "Failed to cancel", "danger");
      } catch { showAlert("Error", "Network error", "danger"); }
    });
  };

  /* ─── Fetch students/assignments when switching tabs ─── */
  useEffect(() => {
    if (activeTab === "students" && adminStudents.length === 0) fetchAdminStudents();
    if (activeTab === "assignments" && adminAssignments.length === 0) fetchAdminAssignments();
  }, [activeTab]);

  /* ─── Stat popup ─── */
  const handleStatClick = async (statType: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
    setStatPopup({ open: true, title: statType, items: [], loading: true });
    try {
      let items: { id: string; label: string; sub?: string }[] = [];
      if (statType === "Total Users") {
        items = users.map((u) => ({ id: u.id, label: u.full_name || u.email, sub: `${u.role} - ${u.email}` }));
      } else if (statType === "Total Students") {
        const res = await fetch(`${API_BASE}/admin/students`, { headers });
        if (res.ok) { const data = await res.json(); items = (data || []).map((s: any) => ({ id: s.id, label: `${s.first_name || ""} ${s.last_name || ""}`.trim() || "Unnamed", sub: [s.school_name, s.primary_guardian_name ? `Guardian: ${s.primary_guardian_name}` : null].filter(Boolean).join(" | ") || undefined })); }
      } else if (statType === "Assessments") {
        const res = await fetch(`${API_BASE}/admin/chat-sessions`, { headers });
        if (res.ok) { const data = await res.json(); items = (data || []).map((s: any) => ({ id: s.id, label: s.student_name || s.parent_email || "Unknown", sub: `${s.status || "unknown"}${s.started_at ? ` - ${new Date(s.started_at).toLocaleDateString()}` : ""}` })); }
      } else if (statType === "Reports") {
        const res = await fetch(`${API_BASE}/admin/psychologist-reports`, { headers });
        if (res.ok) { const data = await res.json(); items = (data || []).map((r: any) => ({ id: r.id, label: r.student_name || "Unknown", sub: `${(r.report_type || "report").replace(/_/g, " ")} - ${r.status || "draft"}` })); }
      } else if (statType === "Parents") {
        items = users.filter((u) => u.role === "PARENT").map((u) => ({ id: u.id, label: u.full_name || u.email, sub: u.email }));
      } else if (statType === "Psychologists") {
        items = users.filter((u) => u.role === "PSYCHOLOGIST").map((u) => ({ id: u.id, label: u.full_name || u.email, sub: u.email }));
      } else if (statType === "Schools") {
        items = users.filter((u) => u.role === "SCHOOL").map((u) => ({ id: u.id, label: u.full_name || u.email, sub: u.organization || u.email }));
      } else if (statType === "Admins") {
        items = users.filter((u) => u.role === "ADMIN").map((u) => ({ id: u.id, label: u.full_name || u.email, sub: u.email }));
      }
      setStatPopup({ open: true, title: statType, items, loading: false });
    } catch {
      setStatPopup({ open: true, title: statType, items: [{ id: "err", label: "Failed to load details" }], loading: false });
    }
  };

  /* ─── User CRUD ─── */
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError("");
    setCreating(true);
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_BASE}/admin/users`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ email: createForm.email, password: createForm.password, full_name: createForm.full_name, role: createForm.role, phone: createForm.phone || null, organization: createForm.organization || null }) });
      if (response.ok) { setShowAddUser(false); setCreateForm({ full_name: "", email: "", password: "", role: "PSYCHOLOGIST", phone: "", organization: "" }); fetchAdminData(token!); }
      else { const data = await response.json().catch(() => null); setCreateError(data?.detail || "Failed to create user"); }
    } catch { setCreateError("Network error."); } finally { setCreating(false); }
  };

  const handleToggleUserStatus = (userId: string, currentStatus: boolean) => {
    showConfirm(currentStatus ? "Deactivate User" : "Activate User", `Are you sure you want to ${currentStatus ? "deactivate" : "activate"} this user?`, "warning", currentStatus ? "Deactivate" : "Activate", async () => {
      try { const token = localStorage.getItem("access_token"); const r = await fetch(`${API_BASE}/admin/users/${userId}/toggle-status`, { method: "PATCH", headers: { Authorization: `Bearer ${token}` } }); if (r.ok) fetchAdminData(token!); else showAlert("Error", "Failed to update status", "danger"); } catch { showAlert("Error", "An error occurred", "danger"); }
    });
  };

  const handleDeleteUser = (userId: string) => {
    showConfirm("Delete User", "This will permanently remove this user and all their data. This cannot be undone.", "danger", "Delete", async () => {
      try { const token = localStorage.getItem("access_token"); const r = await fetch(`${API_BASE}/admin/users/${userId}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } }); if (r.ok) { fetchAdminData(token!); showAlert("Deleted", "User deleted successfully.", "success"); } else showAlert("Error", "Failed to delete user", "danger"); } catch { showAlert("Error", "An error occurred", "danger"); }
    });
  };

  const openEditModal = (u: User) => {
    setSelectedUser(u);
    setEditForm({ full_name: u.full_name || "", email: u.email || "", phone: u.phone || "", organization: u.organization || "", role: u.role || "" });
    setEditError("");
  };

  const handleSaveUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setEditError("");
    setSaving(true);
    try {
      const token = localStorage.getItem("access_token");
      const body: Record<string, string> = {};
      if (editForm.full_name !== (selectedUser.full_name || "")) body.full_name = editForm.full_name;
      if (editForm.email !== (selectedUser.email || "")) body.email = editForm.email;
      if (editForm.phone !== (selectedUser.phone || "")) body.phone = editForm.phone;
      if (editForm.organization !== (selectedUser.organization || "")) body.organization = editForm.organization;
      if (editForm.role !== (selectedUser.role || "")) body.role = editForm.role;
      if (Object.keys(body).length === 0) { setSelectedUser(null); return; }
      const r = await fetch(`${API_BASE}/admin/users/${selectedUser.id}`, { method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify(body) });
      if (r.ok) { setSelectedUser(null); fetchAdminData(token!); }
      else { const data = await r.json().catch(() => null); setEditError(data?.detail || "Failed to update user"); }
    } catch { setEditError("Network error."); } finally { setSaving(false); }
  };

  const handleResetAssessment = async (u: User) => {
    setResetting(u.id);
    try {
      const token = localStorage.getItem("access_token");
      const studentsRes = await fetch(`${API_BASE}/admin/students`, { headers: { Authorization: `Bearer ${token}` } });
      if (!studentsRes.ok) { showAlert("Error", "Failed to fetch students", "danger"); setResetting(null); return; }
      const allStudents = await studentsRes.json();
      const matched = allStudents.filter((s: any) => s.primary_guardian_email === u.email);
      if (matched.length === 0) { showAlert("No Students", "No students found for this parent.", "info"); setResetting(null); return; }
      const names = matched.map((s: any) => `${s.first_name} ${s.last_name}`).join("\n");
      setResetting(null);
      showConfirm("Reset Assessment", `This will reset assessments for:\n${names}\n\nAll chat history will be deleted.`, "danger", "Reset All", async () => {
        setResetting(u.id);
        let totalReset = 0;
        for (const s of matched) {
          const res = await fetch(`${API_BASE}/admin/students/${s.id}/reset-assessment`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
          if (res.ok) { const data = await res.json(); totalReset += data.sessions_reset; }
          else { const err = await res.json().catch(() => null); showAlert("Reset Failed", `Failed for ${s.first_name}: ${err?.detail || "Unknown error"}`, "danger"); }
        }
        showAlert("Reset Complete", `${totalReset} session(s) reset successfully.`, "success");
        fetchAdminData(token!);
        setResetting(null);
      });
    } catch { showAlert("Network Error", "Network error during reset.", "danger"); setResetting(null); }
  };

  const handleLogout = () => { localStorage.removeItem("access_token"); localStorage.removeItem("user"); router.push("/login"); };

  const filteredUsers = filterRole === "all" ? users : users.filter((u) => u.role === filterRole);

  /* ─── Loading state ─── */
  if (loading) {
    return (
      <div className="min-h-screen bg-[#eeeeee] flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-[3px] border-slate-700 border-t-teal-500 rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-[#737373]">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  /* ─── Icons ─── */
  const UserIcon = <svg className="w-5 h-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>;
  const StudentIcon = <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>;
  const AssessmentIcon = <svg className="w-5 h-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" /></svg>;
  const ReportIcon = <svg className="w-5 h-5 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>;

  return (
    <div className="min-h-screen bg-[#f4f4f4]">
      {/* ── Header ── */}
      <header className="bg-white backdrop-blur-xl border-b border-[#dedede] sticky top-0 z-40">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
              </div>
              <div>
                <h1 className="font-serif text-[1.125rem] font-bold text-[#0c888e] leading-none">The Ed Psych Practice</h1>
                <p className="text-[0.5625rem] font-medium text-[#737373] tracking-widest uppercase">Admin Console</p>
              </div>
            </div>

            <nav className="hidden sm:flex items-center gap-1 bg-[#f4f4f4] rounded-lg p-0.5">
              <button onClick={() => setActiveTab("users")} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === "users" ? "bg-[#00acb6] text-white" : "text-[#737373] hover:text-[#333]"}`}>
                Overview
              </button>
              <button onClick={() => setActiveTab("students")} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === "students" ? "bg-[#00acb6] text-white" : "text-[#737373] hover:text-[#333]"}`}>
                Students
              </button>
              <button onClick={() => setActiveTab("assignments")} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === "assignments" ? "bg-[#00acb6] text-white" : "text-[#737373] hover:text-[#333]"}`}>
                Assignments
              </button>
              <button onClick={() => setActiveTab("explorer")} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === "explorer" ? "bg-[#00acb6] text-white" : "text-[#737373] hover:text-[#333]"}`}>
                Data Explorer
              </button>
            </nav>

            <div className="flex items-center gap-3">
              <div className="hidden md:block text-right">
                <p className="text-sm font-medium text-[#333] leading-none">{user?.full_name}</p>
                <p className="text-[0.6875rem] text-[#737373] mt-0.5">{user?.email}</p>
              </div>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white text-[0.6875rem] font-bold">
                {(user?.full_name || "A").charAt(0).toUpperCase()}
              </div>
              <button onClick={handleLogout} className="text-xs font-medium text-[#737373] hover:text-[#e61844] transition-colors">
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* ── Mobile tab bar ── */}
      <div className="sm:hidden flex border-b border-[#dedede] bg-white overflow-x-auto">
        <button onClick={() => setActiveTab("users")} className={`flex-1 py-3 text-xs font-medium text-center border-b-2 transition-colors whitespace-nowrap px-3 ${activeTab === "users" ? "border-[#00acb6] text-[#00acb6]" : "border-transparent text-[#737373]"}`}>Overview</button>
        <button onClick={() => setActiveTab("students")} className={`flex-1 py-3 text-xs font-medium text-center border-b-2 transition-colors whitespace-nowrap px-3 ${activeTab === "students" ? "border-[#00acb6] text-[#00acb6]" : "border-transparent text-[#737373]"}`}>Students</button>
        <button onClick={() => setActiveTab("assignments")} className={`flex-1 py-3 text-xs font-medium text-center border-b-2 transition-colors whitespace-nowrap px-3 ${activeTab === "assignments" ? "border-[#00acb6] text-[#00acb6]" : "border-transparent text-[#737373]"}`}>Assignments</button>
        <button onClick={() => setActiveTab("explorer")} className={`flex-1 py-3 text-xs font-medium text-center border-b-2 transition-colors whitespace-nowrap px-3 ${activeTab === "explorer" ? "border-[#00acb6] text-[#00acb6]" : "border-transparent text-[#737373]"}`}>Explorer</button>
      </div>

      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        {activeTab === "users" ? (
          <>
            {/* ── Page Header ── */}
            <div className="mb-8">
              <h2 className="font-serif text-2xl font-bold text-[#333]">Dashboard</h2>
              <p className="text-sm text-[#737373] mt-1">Platform overview and user management</p>
            </div>

            {/* ── Stats Grid ── */}
            {stats && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <StatCard label="Total Users" value={stats.total_users} icon={UserIcon} color="bg-[#e6f7f8] text-[#00acb6]" onClick={() => handleStatClick("Total Users")} />
                <StatCard label="Students" value={stats.total_students} icon={StudentIcon} color="bg-emerald-50 text-emerald-700" onClick={() => handleStatClick("Total Students")} />
                <StatCard label="Assessments" value={stats.total_assessments} icon={AssessmentIcon} color="bg-[#e6f7f8] text-[#00acb6]" onClick={() => handleStatClick("Assessments")} />
                <StatCard label="Reports" value={stats.total_reports} icon={ReportIcon} color="bg-[#fdecec] text-[#e61844]" onClick={() => handleStatClick("Reports")} />
              </div>
            )}

            {/* ── Role Breakdown ── */}
            {stats && (
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-10">
                {([
                  { key: "PARENT" as const, label: "Parents", color: "border-l-emerald-500 bg-emerald-50", textColor: "text-emerald-700" },
                  { key: "PSYCHOLOGIST" as const, label: "Psychologists", color: "border-l-[#00acb6] bg-[#e6f7f8]", textColor: "text-[#0c888e]" },
                  { key: "SCHOOL" as const, label: "Schools", color: "border-l-sky-500 bg-sky-50", textColor: "text-sky-700" },
                  { key: "ADMIN" as const, label: "Admins", color: "border-l-[#e61844] bg-[#fdecec]", textColor: "text-[#e61844]" },
                ] as const).map((r) => (
                  <button
                    key={r.key}
                    onClick={() => handleStatClick(r.label)}
                    className={`text-left px-4 py-3 rounded-xl border border-[#dedede] border-l-[3px] ${r.color} hover:bg-[#f4f4f4] transition-all`}
                  >
                    <p className="text-[0.625rem] font-semibold text-[#737373] uppercase tracking-wider">{r.label}</p>
                    <p className={`text-2xl font-bold ${r.textColor}`}>{stats.users_by_role[r.key]}</p>
                  </button>
                ))}
              </div>
            )}

            {/* ── User Management ── */}
            <div className="bg-white backdrop-blur-sm rounded-2xl border border-[#dedede] overflow-hidden">
              {/* Table Header */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 px-5 py-4 border-b border-[#dedede]">
                <div>
                  <h3 className="font-serif text-base font-semibold text-[#333]">User Management</h3>
                  <p className="text-xs text-[#737373] mt-0.5">{filteredUsers.length} {filteredUsers.length === 1 ? "user" : "users"}</p>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={filterRole}
                    onChange={(e) => setFilterRole(e.target.value)}
                    className="h-9 px-3 bg-white border border-[#dedede] rounded-lg text-xs font-medium text-[#737373] outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500/50 transition-all [&>option]:bg-white [&>option]:text-[#333]"
                  >
                    <option value="all">All Roles</option>
                    <option value="PARENT">Parents</option>
                    <option value="PSYCHOLOGIST">Psychologists</option>
                    <option value="SCHOOL">Schools</option>
                    <option value="ADMIN">Admins</option>
                  </select>
                  <button
                    onClick={() => setShowAddUser(true)}
                    className="h-9 px-4 bg-[#e61844] text-white text-xs font-medium rounded-lg hover:bg-[#cf0627] transition-colors flex items-center gap-1.5"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4.5v15m7.5-7.5h-15" /></svg>
                    Add User
                  </button>
                </div>
              </div>

              {/* Table */}
              {filteredUsers.length === 0 ? (
                <div className="py-16 text-center">
                  <svg className="w-12 h-12 text-slate-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>
                  <p className="text-sm font-medium text-[#737373]">No users match the selected filter</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-[#dedede]">
                        <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">User</th>
                        <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Role</th>
                        <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider hidden md:table-cell">Details</th>
                        <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Status</th>
                        <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider hidden md:table-cell">Joined</th>
                        <th className="px-5 py-3 text-right text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#dedede]">
                      {filteredUsers.map((u) => (
                        <tr key={u.id} className="hover:bg-white transition-colors group">
                          <td className="px-5 py-3.5">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-[#f4f4f4] flex items-center justify-center text-xs font-semibold text-[#737373] shrink-0">
                                {(u.full_name || u.email).charAt(0).toUpperCase()}
                              </div>
                              <div className="min-w-0">
                                <p className="text-sm font-medium text-[#333] truncate">{u.full_name}</p>
                                <p className="text-[0.6875rem] text-[#737373] truncate">{u.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-3.5"><RoleBadge role={u.role} /></td>
                          <td className="px-5 py-3.5 hidden md:table-cell">
                            <div className="text-sm text-[#737373]">
                              {u.role === "PSYCHOLOGIST" || u.role === "SCHOOL" ? (
                                <>
                                  {u.organization && <p>{u.organization}</p>}
                                  {u.phone && <p className="text-xs text-[#737373] font-mono">{u.phone}</p>}
                                  {!u.organization && !u.phone && "-"}
                                </>
                              ) : (
                                <>
                                  {u.phone ? <p className="font-mono">{u.phone}</p> : <span className="text-slate-600">-</span>}
                                </>
                              )}
                            </div>
                          </td>
                          <td className="px-5 py-3.5">
                            <div className="flex items-center gap-1.5">
                              <div className={`w-1.5 h-1.5 rounded-full ${u.is_active ? "bg-emerald-400" : "bg-[#cccccc]"}`} />
                              <span className="text-xs text-[#737373]">{u.is_active ? "Active" : "Inactive"}</span>
                            </div>
                          </td>
                          <td className="px-5 py-3.5 hidden md:table-cell">
                            <span className="text-xs text-[#737373]">{new Date(u.created_at).toLocaleDateString()}</span>
                          </td>
                          <td className="px-5 py-3.5">
                            <div className="flex items-center justify-end gap-1.5 opacity-50 group-hover:opacity-100 transition-opacity">
                              <button onClick={() => handleToggleUserStatus(u.id, u.is_active)} className="h-7 px-2.5 text-[0.6875rem] font-medium rounded-md border border-[#dedede] text-[#737373] hover:bg-[#f4f4f4] hover:text-[#333] transition-colors" title={u.is_active ? "Deactivate" : "Activate"}>
                                {u.is_active ? "Deactivate" : "Activate"}
                              </button>
                              {u.role === "PARENT" && (
                                <button onClick={() => handleResetAssessment(u)} disabled={resetting === u.id} className="h-7 px-2.5 text-[0.6875rem] font-medium rounded-md border border-amber-300 text-amber-700 hover:bg-amber-50 transition-colors disabled:opacity-40" title="Reset assessment">
                                  {resetting === u.id ? "..." : "Reset"}
                                </button>
                              )}
                              <button onClick={() => openEditModal(u)} className="h-7 px-2.5 text-[0.6875rem] font-medium rounded-md border border-teal-300 text-teal-700 hover:bg-teal-50 transition-colors" title="Edit user">
                                Edit
                              </button>
                              <button onClick={() => handleDeleteUser(u.id)} className="h-7 w-7 flex items-center justify-center rounded-md border border-red-300 text-red-700 hover:bg-red-50 transition-colors" title="Delete user">
                                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        ) : activeTab === "students" ? (
          /* ── Students Tab ── */
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-serif text-2xl font-bold text-[#333]">Student Management</h2>
                <p className="text-sm text-[#737373] mt-1">Create students and link parents/schools</p>
              </div>
              <button onClick={() => { setShowCreateStudent(true); }} className="h-9 px-4 bg-[#e61844] text-white text-xs font-medium rounded-lg hover:bg-[#cf0627] transition-colors flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4.5v15m7.5-7.5h-15" /></svg>
                Add Student
              </button>
            </div>

            {studentsLoading ? (
              <div className="flex justify-center py-16"><div className="w-6 h-6 border-[3px] border-slate-200 border-t-primary rounded-full animate-spin" /></div>
            ) : adminStudents.length === 0 ? (
              <div className="text-center py-16 text-[#737373]">No students yet. Click &quot;Add Student&quot; to create one.</div>
            ) : (
              <div className="bg-white backdrop-blur-sm rounded-2xl border border-[#dedede] overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead><tr className="border-b border-[#dedede]">
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Student</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Grade</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">School</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Parent/Guardian</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Status</th>
                      <th className="px-5 py-3 text-right text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Actions</th>
                    </tr></thead>
                    <tbody className="divide-y divide-[#dedede]">
                      {adminStudents.map((s: any) => (
                        <tr key={s.id} className="hover:bg-white transition-colors group">
                          <td className="px-5 py-3.5">
                            <p className="text-sm font-medium text-[#333]">{s.first_name} {s.last_name}</p>
                          </td>
                          <td className="px-5 py-3.5 text-sm text-[#737373]">{s.grade || "-"}</td>
                          <td className="px-5 py-3.5 text-sm text-[#737373]">{s.school_name || "-"}</td>
                          <td className="px-5 py-3.5">
                            {s.guardians && s.guardians.length > 0 ? (
                              <div>
                                <p className="text-sm text-[#333]">{s.guardians[0].name}</p>
                                <p className="text-[0.6875rem] text-[#737373]">{s.guardians[0].email}</p>
                              </div>
                            ) : <span className="text-slate-600">No guardian</span>}
                          </td>
                          <td className="px-5 py-3.5">
                            {s.assignment_status ? (
                              <div className="flex items-center gap-2">
                                <span className={`px-2 py-0.5 rounded-full text-[0.625rem] font-semibold ${s.assignment_status === "completed" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                                  {s.assignment_status.toUpperCase()}
                                </span>
                                {s.progress_percentage > 0 && s.assignment_status !== "completed" && (
                                  <span className="text-[0.6875rem] text-[#737373]">{s.progress_percentage}%</span>
                                )}
                              </div>
                            ) : <span className="text-[0.6875rem] text-slate-600">No assignment</span>}
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <a href={`/student/${s.id}/workspace`} className="text-[0.6875rem] font-medium text-[#00acb6] hover:text-[#0c888e]">Reports Workspace</a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : activeTab === "assignments" ? (
          /* ── Assignments Tab ── */
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="font-serif text-2xl font-bold text-[#333]">Assessment Assignments</h2>
                <p className="text-sm text-[#737373] mt-1">Assign assessments and manage magic links</p>
              </div>
              <button onClick={() => { setShowAssignForm(true); fetchStudentsForAssign(); }} className="h-9 px-4 bg-[#e61844] text-white text-xs font-medium rounded-lg hover:bg-[#cf0627] transition-colors flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4.5v15m7.5-7.5h-15" /></svg>
                New Assignment
              </button>
            </div>

            {assignmentsLoading ? (
              <div className="flex justify-center py-16"><div className="w-6 h-6 border-[3px] border-slate-200 border-t-primary rounded-full animate-spin" /></div>
            ) : adminAssignments.length === 0 ? (
              <div className="text-center py-16 text-[#737373]">No assignments yet. Click &quot;New Assignment&quot; to create one.</div>
            ) : (
              <div className="bg-white backdrop-blur-sm rounded-2xl border border-[#dedede] overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead><tr className="border-b border-[#dedede]">
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Student</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Assigned To</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Status</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Due Date</th>
                      <th className="px-5 py-3 text-left text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Assigned</th>
                      <th className="px-5 py-3 text-right text-[0.6875rem] font-semibold text-[#737373] uppercase tracking-wider">Actions</th>
                    </tr></thead>
                    <tbody className="divide-y divide-[#dedede]">
                      {adminAssignments.map((a: any) => (
                        <tr key={a.id} className="hover:bg-white transition-colors group">
                          <td className="px-5 py-3.5">
                            <p className="text-sm font-medium text-[#333]">{a.student ? `${a.student.first_name || ""} ${a.student.last_name || ""}`.trim() || "Unknown" : "Unknown"}</p>
                          </td>
                          <td className="px-5 py-3.5">
                            <p className="text-sm text-[#333]">{a.assigned_to?.name || "Unknown"}</p>
                            <p className="text-[0.6875rem] text-[#737373]">{a.assigned_to?.email || ""}</p>
                          </td>
                          <td className="px-5 py-3.5">
                            <span className={`px-2 py-0.5 rounded-full text-[0.625rem] font-semibold ${
                              a.status === "completed" ? "bg-emerald-100 text-emerald-700" :
                              a.status === "cancelled" ? "bg-[#737373]/20 text-[#737373]" :
                              "bg-amber-100 text-amber-700"
                            }`}>
                              {(a.status || "").toUpperCase()}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-sm text-[#737373]">{a.due_date ? new Date(a.due_date).toLocaleDateString() : "No deadline"}</td>
                          <td className="px-5 py-3.5 text-sm text-[#737373]">{a.assigned_at ? new Date(a.assigned_at).toLocaleDateString() : "-"}</td>
                          <td className="px-5 py-3.5">
                            <div className="flex items-center justify-end gap-1.5">
                              {(a.status || "").toLowerCase() === "assigned" && (
                                <>
                                  <button onClick={() => handleResendInvite(a.id)} className="h-7 px-2.5 text-[0.6875rem] font-medium rounded-md border border-teal-300 text-teal-700 hover:bg-teal-50 transition-colors">Resend Link</button>
                                  <button onClick={() => handleCancelAssignment(a.id)} className="h-7 px-2.5 text-[0.6875rem] font-medium rounded-md border border-red-300 text-red-700 hover:bg-red-50 transition-colors">Cancel</button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* ── Data Explorer Tab ── */
          <div>
            <div className="mb-6">
              <h2 className="font-serif text-2xl font-bold text-[#333]">Data Explorer</h2>
              <p className="text-sm text-[#737373] mt-1">Read-only view of all database records</p>
            </div>
            <DataExplorer />
          </div>
        )}
      </main>

      {/* ── Add User Modal ── */}
      <ModalOverlay open={showAddUser} onClose={() => { setShowAddUser(false); setCreateError(""); }}>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-on-background">Add New User</h3>
          <p className="text-xs text-[#737373] mt-1 mb-5">Create an account for any role</p>
          {createError && <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-lg text-red-600 text-xs font-medium">{createError}</div>}
          <form onSubmit={handleCreateUser} className="space-y-3">
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Role</label>
              <select value={createForm.role} onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                <option value="PSYCHOLOGIST">Psychologist</option>
                <option value="SCHOOL">School</option>
                <option value="PARENT">Parent</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Full Name</label>
              <input type="text" required value={createForm.full_name} onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" placeholder="Dr. Jane Smith" />
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Email</label>
              <input type="email" required value={createForm.email} onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" placeholder="jane@example.com" />
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Password</label>
              <input type="text" required minLength={8} value={createForm.password} onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" placeholder="Min 8 characters" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Phone</label>
                <input type="tel" value={createForm.phone} onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" placeholder="+44 7700..." />
              </div>
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Organization</label>
                <input type="text" value={createForm.organization} onChange={(e) => setCreateForm({ ...createForm, organization: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" placeholder="Clinic name" />
              </div>
            </div>
            <div className="flex gap-3 pt-3">
              <button type="button" onClick={() => { setShowAddUser(false); setCreateError(""); }} className="flex-1 h-10 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancel</button>
              <button type="submit" disabled={creating} className="flex-1 h-10 text-sm font-medium text-white bg-[#e61844] rounded hover:bg-[#cf0627] transition-colors disabled:opacity-50 shadow-sm">
                {creating ? "Creating..." : "Create User"}
              </button>
            </div>
          </form>
        </div>
      </ModalOverlay>

      {/* ── Edit User Modal ── */}
      <ModalOverlay open={!!selectedUser} onClose={() => { setSelectedUser(null); setEditError(""); }}>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-on-background">Edit User</h3>
          <p className="text-xs text-[#737373] mt-1 mb-5">Update details for {selectedUser?.full_name}</p>
          {editError && <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-lg text-red-600 text-xs font-medium">{editError}</div>}
          <form onSubmit={handleSaveUser} className="space-y-3">
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Full Name</label>
              <input type="text" value={editForm.full_name} onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Email</label>
              <input type="email" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Phone</label>
                <input type="tel" value={editForm.phone} onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
              </div>
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Organization</label>
                <input type="text" value={editForm.organization} onChange={(e) => setEditForm({ ...editForm, organization: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
              </div>
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Role</label>
              <select value={editForm.role} onChange={(e) => setEditForm({ ...editForm, role: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                <option value="PARENT">Parent</option>
                <option value="PSYCHOLOGIST">Psychologist</option>
                <option value="SCHOOL">School</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
            <div className="flex gap-3 pt-3">
              <button type="button" onClick={() => { setSelectedUser(null); setEditError(""); }} className="flex-1 h-10 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancel</button>
              <button type="submit" disabled={saving} className="flex-1 h-10 text-sm font-medium text-white bg-[#e61844] rounded hover:bg-[#cf0627] transition-colors disabled:opacity-50 shadow-sm">
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      </ModalOverlay>

      {/* ── Stat Detail Popup ── */}
      <ModalOverlay open={statPopup.open} onClose={() => setStatPopup((s) => ({ ...s, open: false }))} maxW="max-w-lg">
        <div>
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <h3 className="text-base font-semibold text-on-background">{statPopup.title}</h3>
            <button onClick={() => setStatPopup((s) => ({ ...s, open: false }))} className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center transition-colors">
              <svg className="w-4 h-4 text-[#737373]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div className="px-5 py-4 max-h-[50vh] overflow-y-auto">
            {statPopup.loading ? (
              <div className="flex items-center justify-center py-10">
                <div className="w-6 h-6 border-[3px] border-slate-200 border-t-primary rounded-full animate-spin" />
              </div>
            ) : statPopup.items.length === 0 ? (
              <p className="text-center text-sm text-[#737373] py-10">No records found</p>
            ) : (
              <div className="space-y-1.5">
                {statPopup.items.map((item, idx) => (
                  <div key={item.id || idx} className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-50 transition-colors">
                    <div className="w-7 h-7 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[0.6875rem] font-semibold shrink-0">
                      {idx + 1}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-on-background truncate">{item.label}</p>
                      {item.sub && <p className="text-[0.6875rem] text-[#737373] truncate">{item.sub}</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="px-5 py-3 border-t border-slate-100">
            <p className="text-[0.6875rem] text-[#737373] text-center">{statPopup.loading ? "" : `${statPopup.items.length} record${statPopup.items.length !== 1 ? "s" : ""}`}</p>
          </div>
        </div>
      </ModalOverlay>

      {/* ── Create Student Modal ── */}
      <ModalOverlay open={showCreateStudent} onClose={() => { setShowCreateStudent(false); setStudentFormError(""); }} maxW="max-w-lg">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-on-background">Create New Student</h3>
          <p className="text-xs text-[#737373] mt-1 mb-5">Enter student and parent/guardian details</p>
          {studentFormError && <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-lg text-red-600 text-xs font-medium">{studentFormError}</div>}
          <form onSubmit={handleCreateStudent} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">First Name</label>
                <input type="text" required value={studentForm.student_first_name} onChange={(e) => setStudentForm({ ...studentForm, student_first_name: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
              </div>
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Last Name</label>
                <input type="text" required value={studentForm.student_last_name} onChange={(e) => setStudentForm({ ...studentForm, student_last_name: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Date of Birth</label>
                <input type="date" required value={studentForm.date_of_birth} onChange={(e) => setStudentForm({ ...studentForm, date_of_birth: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
              </div>
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Grade/Year</label>
                <input type="text" value={studentForm.grade} onChange={(e) => setStudentForm({ ...studentForm, grade: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" placeholder="Year 7" />
              </div>
              <div>
                <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Gender</label>
                <select value={studentForm.gender} onChange={(e) => setStudentForm({ ...studentForm, gender: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                  <option value="">Select...</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">School Name</label>
              <input type="text" value={studentForm.school_name} onChange={(e) => setStudentForm({ ...studentForm, school_name: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            </div>

            <div className="border-t border-slate-200 pt-3 mt-3">
              <h4 className="text-sm font-semibold text-on-background mb-3">Parent/Guardian</h4>
              {studentForm.parents.map((p, idx) => (
                <div key={idx} className="space-y-2 mb-3 p-3 bg-slate-50 rounded-lg">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Full Name</label>
                      <input type="text" required value={p.full_name} onChange={(e) => { const parents = [...studentForm.parents]; parents[idx] = { ...p, full_name: e.target.value }; setStudentForm({ ...studentForm, parents }); }} className="w-full h-9 px-3 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                    </div>
                    <div>
                      <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Email</label>
                      <input type="email" required value={p.email} onChange={(e) => { const parents = [...studentForm.parents]; parents[idx] = { ...p, email: e.target.value }; setStudentForm({ ...studentForm, parents }); }} className="w-full h-9 px-3 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Phone</label>
                      <input type="tel" value={p.phone} onChange={(e) => { const parents = [...studentForm.parents]; parents[idx] = { ...p, phone: e.target.value }; setStudentForm({ ...studentForm, parents }); }} className="w-full h-9 px-3 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20" />
                    </div>
                    <div>
                      <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Relationship</label>
                      <select value={p.relationship} onChange={(e) => { const parents = [...studentForm.parents]; parents[idx] = { ...p, relationship: e.target.value }; setStudentForm({ ...studentForm, parents }); }} className="w-full h-9 px-3 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20">
                        <option value="Mother">Mother</option>
                        <option value="Father">Father</option>
                        <option value="Guardian">Guardian</option>
                        <option value="Grandparent">Grandparent</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Type</label>
                      <select value={p.type} onChange={(e) => { const parents = [...studentForm.parents]; parents[idx] = { ...p, type: e.target.value }; setStudentForm({ ...studentForm, parents }); }} className="w-full h-9 px-3 bg-white border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20">
                        <option value="parent">Parent</option>
                        <option value="school">School</option>
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3 pt-3">
              <button type="button" onClick={() => { setShowCreateStudent(false); setStudentFormError(""); }} className="flex-1 h-10 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancel</button>
              <button type="submit" disabled={creatingStudent} className="flex-1 h-10 text-sm font-medium text-white bg-[#e61844] rounded hover:bg-[#cf0627] transition-colors disabled:opacity-50 shadow-sm">
                {creatingStudent ? "Creating..." : "Create Student"}
              </button>
            </div>
          </form>
        </div>
      </ModalOverlay>

      {/* ── New Assignment Modal ── */}
      <ModalOverlay open={showAssignForm} onClose={() => { setShowAssignForm(false); setAssignFormError(""); }} maxW="max-w-md">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-on-background">New Assignment</h3>
          <p className="text-xs text-[#737373] mt-1 mb-5">Assign assessment and send magic link</p>
          {assignFormError && <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-lg text-red-600 text-xs font-medium">{assignFormError}</div>}
          <form onSubmit={handleAssign} className="space-y-3">
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Student</label>
              <select required value={assignForm.student_id} onChange={(e) => handleStudentSelectForAssign(e.target.value)} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                <option value="">Select student...</option>
                {assignStudents.map((s: any) => (
                  <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Assign To (Parent/Guardian)</label>
              <select required value={assignForm.parent_id} onChange={(e) => setAssignForm({ ...assignForm, parent_id: e.target.value })} className="w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
                <option value="">Select parent/guardian...</option>
                {selectedStudentGuardians.map((g: any) => (
                  <option key={g.id} value={g.id}>{g.name} ({g.email}) - {g.relationship}</option>
                ))}
              </select>
              {assignForm.student_id && selectedStudentGuardians.length === 0 && (
                <p className="text-[0.6875rem] text-amber-500 mt-1">No guardians linked to this student. Add a guardian first.</p>
              )}
            </div>
            <div>
              <label className="block text-[0.6875rem] font-medium text-[#737373] mb-1">Notes (optional)</label>
              <textarea value={assignForm.notes} onChange={(e) => setAssignForm({ ...assignForm, notes: e.target.value })} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none" rows={2} placeholder="Any notes for the parent..." />
            </div>
            <div className="flex gap-3 pt-3">
              <button type="button" onClick={() => { setShowAssignForm(false); setAssignFormError(""); }} className="flex-1 h-10 text-sm font-medium text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">Cancel</button>
              <button type="submit" disabled={assigning} className="flex-1 h-10 text-sm font-medium text-white bg-[#e61844] rounded hover:bg-[#cf0627] transition-colors disabled:opacity-50 shadow-sm">
                {assigning ? "Assigning..." : "Assign & Send Link"}
              </button>
            </div>
          </form>
        </div>
      </ModalOverlay>

      {/* ── Dialog ── */}
      <Dialog open={dialog.open} title={dialog.title} message={dialog.message} variant={dialog.variant} confirmLabel={dialog.confirmLabel} cancelLabel={dialog.cancelLabel} onConfirm={dialog.onConfirm} onCancel={dialog.onCancel} />
    </div>
  );
}
