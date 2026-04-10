// Shared types for the admin Data Explorer section.
// Fields are intentionally permissive — admin endpoints return full DB rows
// and we only depend on a stable subset for display.

export type DataExplorerTab =
  | "students"
  | "assessments"
  | "reports"
  | "cognitive"
  | "iq";

export interface AdminStudentRow {
  id: string;
  first_name: string;
  last_name: string;
  grade_level: string | null;
  school_name: string | null;
  date_of_birth?: string | null;
  created_at: string;
  primary_guardian?: {
    id: string;
    name: string;
    email: string;
    relationship_type?: string | null;
  } | null;
  sessions_count?: number | null;
  // Allow extra fields for the drawer JSON view.
  [key: string]: any;
}

export interface AdminAssessmentRow {
  id: string;
  student_id?: string | null;
  student_name?: string | null;
  parent_email?: string | null;
  status: string;
  flow_type?: string | null;
  current_step?: string | number | null;
  started_at?: string | null;
  last_activity_at?: string | null;
  created_at?: string | null;
  context_data?: any;
  [key: string]: any;
}

export type ReportType =
  | "background_summary"
  | "cognitive_report"
  | "unified_insights";

export interface AdminReportRow {
  id: string;
  student_id?: string | null;
  student_name?: string | null;
  report_type: ReportType | string;
  status: string;
  content_preview?: string | null;
  content_markdown?: string | null;
  source_data?: any;
  created_at: string;
  updated_at?: string | null;
  [key: string]: any;
}

export interface AdminCognitiveRow {
  id: string;
  student_id?: string | null;
  student_name?: string | null;
  test_name?: string | null;
  test_date?: string | null;
  parsed_scores?: {
    full_scale_iq?: number | null;
    [key: string]: any;
  } | null;
  confidence?: number | null;
  requires_review?: boolean | null;
  ocr_text_length?: number | null;
  created_at: string;
  [key: string]: any;
}

export interface AdminIqUploadRow {
  id: string;
  student_id?: string | null;
  student_name?: string | null;
  filename: string;
  file_size?: number | null;
  status?: string | null;
  uploaded_by_name?: string | null;
  uploaded_by_email?: string | null;
  uploaded_at?: string | null;
  created_at?: string | null;
  [key: string]: any;
}
