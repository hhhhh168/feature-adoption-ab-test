-- A/B Testing Database Schema
-- Two-Tier Verification Feature Experiment

-- ============================================================
-- TABLE 1: users
-- Core user demographics and account information
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signup_date TIMESTAMP NOT NULL,
    age INTEGER CHECK (age BETWEEN 18 AND 60),
    gender VARCHAR(20),
    location VARCHAR(100),
    education_level VARCHAR(50),
    account_type VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE 2: user_pre_metrics
-- Pre-experiment metrics for CUPED variance reduction
-- ============================================================
CREATE TABLE IF NOT EXISTS user_pre_metrics (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    pre_period_start DATE NOT NULL,
    pre_period_end DATE NOT NULL,
    pre_sessions_count INTEGER DEFAULT 0,
    pre_matches_count INTEGER DEFAULT 0,
    pre_messages_sent INTEGER DEFAULT 0,
    pre_total_time_minutes INTEGER DEFAULT 0,
    pre_profile_views INTEGER DEFAULT 0
);

-- ============================================================
-- TABLE 3: experiments
-- Experiment metadata and configuration
-- ============================================================
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id VARCHAR(100) PRIMARY KEY,
    experiment_name VARCHAR(200) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    description TEXT,
    hypothesis TEXT,
    target_metric VARCHAR(100),
    minimum_detectable_effect DECIMAL(5,4),
    alpha DECIMAL(3,2) DEFAULT 0.05,
    power DECIMAL(3,2) DEFAULT 0.80,
    status VARCHAR(20) DEFAULT 'active'
);

-- ============================================================
-- TABLE 4: experiment_assignments
-- User variant assignments (control/treatment)
-- ============================================================
CREATE TABLE IF NOT EXISTS experiment_assignments (
    assignment_id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    experiment_id VARCHAR(100) REFERENCES experiments(experiment_id),
    variant VARCHAR(50) NOT NULL,
    assignment_timestamp TIMESTAMP DEFAULT NOW(),
    device_type VARCHAR(50),
    app_version VARCHAR(20),
    UNIQUE(user_id, experiment_id)
);

-- ============================================================
-- TABLE 5: events
-- Event stream for user interactions
-- ============================================================
CREATE TABLE IF NOT EXISTS events (
    event_id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    event_type VARCHAR(100) NOT NULL,
    event_timestamp TIMESTAMP DEFAULT NOW(),
    session_id UUID,
    event_properties JSONB,
    experiment_id VARCHAR(100),
    variant VARCHAR(50)
);

-- ============================================================
-- TABLE 6: verification_attempts
-- Track verification flow attempts and completions
-- ============================================================
CREATE TABLE IF NOT EXISTS verification_attempts (
    attempt_id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    verification_tier INTEGER CHECK (verification_tier IN (1, 2)),
    attempt_timestamp TIMESTAMP DEFAULT NOW(),
    completion_status VARCHAR(20),
    completion_timestamp TIMESTAMP,
    time_to_complete_seconds INTEGER,
    failure_reason VARCHAR(200),
    experiment_id VARCHAR(100),
    variant VARCHAR(50)
);

-- ============================================================
-- TABLE 7: verification_status
-- Current verification status for each user
-- ============================================================
CREATE TABLE IF NOT EXISTS verification_status (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    tier1_verified BOOLEAN DEFAULT FALSE,
    tier1_verification_date TIMESTAMP,
    tier1_domain VARCHAR(100),
    tier2_verified BOOLEAN DEFAULT FALSE,
    tier2_verification_date TIMESTAMP,
    verification_badge_type VARCHAR(50),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES: Optimize query performance
-- ============================================================

-- Events table indexes
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_experiment ON events(experiment_id, variant);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);

-- Experiment assignments indexes
CREATE INDEX IF NOT EXISTS idx_assignments_experiment ON experiment_assignments(experiment_id);
CREATE INDEX IF NOT EXISTS idx_assignments_variant ON experiment_assignments(variant);
CREATE INDEX IF NOT EXISTS idx_assignments_user ON experiment_assignments(user_id);

-- Verification attempts indexes
CREATE INDEX IF NOT EXISTS idx_verification_attempts_user ON verification_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_verification_attempts_experiment ON verification_attempts(experiment_id, variant);
CREATE INDEX IF NOT EXISTS idx_verification_attempts_tier ON verification_attempts(verification_tier);
CREATE INDEX IF NOT EXISTS idx_verification_attempts_status ON verification_attempts(completion_status);

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_signup_date ON users(signup_date);
CREATE INDEX IF NOT EXISTS idx_users_account_type ON users(account_type);
