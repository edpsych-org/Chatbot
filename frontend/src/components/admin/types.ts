export type DataExplorerTab = "students";

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
  [key: string]: any;
}
