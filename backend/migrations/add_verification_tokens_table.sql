-- Migration: Add verification_tokens table for multi-layer parent verification
-- Created: 2026-04-01
-- Description: Stores secure tokens and OTP codes for parent assessment access verification

CREATE TABLE IF NOT EXISTS verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Secure token (URL-safe, 32 characters)
    secure_token VARCHAR(255) UNIQUE NOT NULL,

    -- OTP code (6 digits)
    otp_code VARCHAR(6) NOT NULL,

    -- Related entities
    assignment_id UUID NOT NULL REFERENCES assessment_assignments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    parent_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Verification status
    is_otp_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_dob_verified BOOLEAN DEFAULT FALSE NOT NULL,
    is_fully_verified BOOLEAN DEFAULT FALSE NOT NULL,

    -- Expiration
    expires_at TIMESTAMP NOT NULL,

    -- Verification attempts tracking
    otp_attempts VARCHAR DEFAULT '0' NOT NULL,
    dob_attempts VARCHAR DEFAULT '0' NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    otp_verified_at TIMESTAMP,
    dob_verified_at TIMESTAMP,
    fully_verified_at TIMESTAMP,

    -- Metadata
    ip_address VARCHAR(50),
    user_agent TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_verification_tokens_secure_token ON verification_tokens(secure_token);
CREATE INDEX IF NOT EXISTS idx_verification_tokens_assignment_id ON verification_tokens(assignment_id);
CREATE INDEX IF NOT EXISTS idx_verification_tokens_student_id ON verification_tokens(student_id);
CREATE INDEX IF NOT EXISTS idx_verification_tokens_parent_user_id ON verification_tokens(parent_user_id);
CREATE INDEX IF NOT EXISTS idx_verification_tokens_expires_at ON verification_tokens(expires_at);

-- Add comment to table
COMMENT ON TABLE verification_tokens IS 'Multi-layer verification tokens for secure parent assessment access';
