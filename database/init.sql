-- EdPsych AI Database Initialization Script
-- PostgreSQL 16

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search

-- Set timezone
SET timezone = 'UTC';

-- ==================== USERS TABLE ====================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('parent', 'school', 'psychologist', 'admin')),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    organization VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- ==================== STUDENTS TABLE ====================
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    school_name VARCHAR(255),
    year_group VARCHAR(50),
    created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_students_created_by ON students(created_by_user_id);
CREATE INDEX idx_students_name ON students(first_name, last_name);

-- ==================== ASSESSMENT SESSIONS TABLE ====================
CREATE TABLE assessment_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'submitted')),
    progress_percentage INT DEFAULT 0,
    current_section VARCHAR(100),
    resume_token VARCHAR(255) UNIQUE,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    submitted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_student ON assessment_sessions(student_id);
CREATE INDEX idx_sessions_parent ON assessment_sessions(parent_id);
CREATE INDEX idx_sessions_status ON assessment_sessions(status);
CREATE INDEX idx_sessions_resume_token ON assessment_sessions(resume_token);

-- ==================== CHATBOT QUESTIONS TABLE ====================
CREATE TABLE chatbot_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_number INT NOT NULL UNIQUE,
    section VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL CHECK (question_type IN ('multiple_choice', 'text', 'yes_no', 'scale')),
    options JSONB,  -- For MCQ options
    is_required BOOLEAN DEFAULT TRUE,
    help_text TEXT,
    order_index INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_questions_section ON chatbot_questions(section);
CREATE INDEX idx_questions_order ON chatbot_questions(order_index);

-- ==================== CHATBOT ANSWERS TABLE ====================
CREATE TABLE chatbot_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES chatbot_questions(id) ON DELETE CASCADE,
    answer_text TEXT,
    answer_data JSONB,  -- For structured answers
    is_complete BOOLEAN DEFAULT FALSE,
    answered_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, question_id)
);

CREATE INDEX idx_answers_session ON chatbot_answers(session_id);
CREATE INDEX idx_answers_question ON chatbot_answers(question_id);

-- ==================== IQ TEST UPLOADS TABLE ====================
CREATE TABLE iq_test_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    uploaded_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100),
    minio_bucket VARCHAR(100),
    minio_object_key VARCHAR(500),
    upload_status VARCHAR(50) DEFAULT 'uploaded' CHECK (upload_status IN ('uploaded', 'processing', 'completed', 'failed')),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

CREATE INDEX idx_iq_uploads_student ON iq_test_uploads(student_id);
CREATE INDEX idx_iq_uploads_user ON iq_test_uploads(uploaded_by_user_id);
CREATE INDEX idx_iq_uploads_status ON iq_test_uploads(upload_status);

-- ==================== COGNITIVE PROFILES TABLE ====================
CREATE TABLE cognitive_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    iq_test_upload_id UUID REFERENCES iq_test_uploads(id) ON DELETE SET NULL,
    test_name VARCHAR(100) NOT NULL,  -- WISC-V, WIAT-III, etc.
    test_date DATE,
    administered_by VARCHAR(255),
    raw_ocr_text TEXT,
    parsed_scores JSONB NOT NULL,  -- Structured test scores
    percentiles JSONB,
    confidence_score FLOAT,  -- OCR/parsing confidence
    requires_review BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cognitive_student ON cognitive_profiles(student_id);
CREATE INDEX idx_cognitive_test ON cognitive_profiles(iq_test_upload_id);

-- ==================== AI GENERATION JOBS TABLE ====================
CREATE TABLE ai_generation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN ('profile', 'impact', 'recommendations')),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    input_data JSONB NOT NULL,
    output_text TEXT,
    model_used VARCHAR(100),
    tokens_used INT,
    generation_time_seconds FLOAT,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_ai_jobs_student ON ai_generation_jobs(student_id);
CREATE INDEX idx_ai_jobs_session ON ai_generation_jobs(session_id);
CREATE INDEX idx_ai_jobs_status ON ai_generation_jobs(status);
CREATE INDEX idx_ai_jobs_type ON ai_generation_jobs(job_type);

-- ==================== GENERATED REPORTS TABLE ====================
CREATE TABLE generated_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES assessment_sessions(id) ON DELETE CASCADE,
    profile_job_id UUID REFERENCES ai_generation_jobs(id),
    impact_job_id UUID REFERENCES ai_generation_jobs(id),
    recommendations_job_id UUID REFERENCES ai_generation_jobs(id),
    profile_text TEXT,
    impact_text TEXT,
    recommendations_text TEXT,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'rejected')),
    generated_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_generated_reports_student ON generated_reports(student_id);
CREATE INDEX idx_generated_reports_session ON generated_reports(session_id);
CREATE INDEX idx_generated_reports_status ON generated_reports(status);

-- ==================== REPORT REVIEWS TABLE ====================
CREATE TABLE report_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES generated_reports(id) ON DELETE CASCADE,
    reviewed_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    review_status VARCHAR(50) NOT NULL CHECK (review_status IN ('pending', 'approved', 'changes_requested')),
    edited_profile_text TEXT,
    edited_impact_text TEXT,
    edited_recommendations_text TEXT,
    reviewer_notes TEXT,
    reviewed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reviews_report ON report_reviews(report_id);
CREATE INDEX idx_reviews_reviewer ON report_reviews(reviewed_by_user_id);
CREATE INDEX idx_reviews_status ON report_reviews(review_status);

-- ==================== FINAL REPORTS TABLE ====================
CREATE TABLE final_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    report_id UUID NOT NULL REFERENCES generated_reports(id) ON DELETE CASCADE,
    review_id UUID REFERENCES report_reviews(id) ON DELETE SET NULL,
    pdf_file_path VARCHAR(500),
    docx_file_path VARCHAR(500),
    minio_pdf_key VARCHAR(500),
    minio_docx_key VARCHAR(500),
    report_date DATE NOT NULL,
    generated_by_user_id UUID NOT NULL REFERENCES users(id),
    approved_by_user_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'generated' CHECK (status IN ('generated', 'sent', 'archived')),
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP
);

CREATE INDEX idx_final_reports_student ON final_reports(student_id);
CREATE INDEX idx_final_reports_report ON final_reports(report_id);
CREATE INDEX idx_final_reports_status ON final_reports(status);

-- ==================== AUDIT LOG TABLE ====================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);

-- ==================== TRIGGERS FOR UPDATED_AT ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON assessment_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_answers_updated_at BEFORE UPDATE ON chatbot_answers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cognitive_updated_at BEFORE UPDATE ON cognitive_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON generated_reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== INITIAL DATA ====================
-- Insert default admin user (password: admin123)
INSERT INTO users (email, password_hash, role, full_name, is_verified) VALUES
('admin@edpsych.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEg7IW', 'admin', 'System Administrator', TRUE);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully!';
    RAISE NOTICE 'Default admin user: admin@edpsych.local / admin123';
END $$;
