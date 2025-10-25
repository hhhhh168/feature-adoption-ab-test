-- Materialized Views for WorkHeart A/B Testing
-- Pre-aggregated metrics for performance optimization

-- ============================================================
-- VIEW 1: user_engagement_metrics
-- Aggregated engagement metrics per user
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS user_engagement_metrics AS
SELECT
    e.user_id,
    e.experiment_id,
    e.variant,
    COUNT(DISTINCT session_id) as sessions_count,
    COUNT(*) FILTER (WHERE event_type = 'match') as matches_count,
    COUNT(*) FILTER (WHERE event_type = 'message_sent') as messages_sent,
    COUNT(*) FILTER (WHERE event_type = 'message_received') as messages_received,
    COUNT(*) FILTER (WHERE event_type = 'profile_view') as profile_views,
    SUM((event_properties->>'duration_seconds')::INTEGER) as total_time_seconds,
    MIN(event_timestamp) as first_event,
    MAX(event_timestamp) as last_event,
    DATE(MAX(event_timestamp)) - DATE(MIN(event_timestamp)) as days_active
FROM events e
WHERE experiment_id IS NOT NULL
GROUP BY e.user_id, e.experiment_id, e.variant;

-- Index for fast lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_engagement_metrics_composite
ON user_engagement_metrics(user_id, experiment_id);

CREATE INDEX IF NOT EXISTS idx_engagement_metrics_variant
ON user_engagement_metrics(experiment_id, variant);

-- ============================================================
-- VIEW 2: daily_experiment_metrics
-- Daily aggregated metrics for time series analysis
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_experiment_metrics AS
SELECT
    experiment_id,
    variant,
    DATE(event_timestamp) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(*) FILTER (WHERE event_type = 'match') as total_matches,
    COUNT(*) FILTER (WHERE event_type = 'message_sent') as total_messages,
    COUNT(*) FILTER (WHERE event_type = 'profile_view') as total_profile_views,
    AVG((event_properties->>'duration_seconds')::INTEGER) as avg_session_duration
FROM events
WHERE experiment_id IS NOT NULL
GROUP BY experiment_id, variant, DATE(event_timestamp);

-- Index for time series queries
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date
ON daily_experiment_metrics(experiment_id, variant, date);

-- ============================================================
-- VIEW 3: verification_funnel_metrics
-- Aggregated verification funnel metrics
-- ============================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS verification_funnel_metrics AS
WITH tier1_stats AS (
    SELECT
        experiment_id,
        variant,
        COUNT(DISTINCT user_id) as tier1_attempts,
        COUNT(DISTINCT user_id) FILTER (WHERE completion_status = 'completed') as tier1_completions,
        AVG(time_to_complete_seconds) FILTER (WHERE completion_status = 'completed') as avg_tier1_time
    FROM verification_attempts
    WHERE verification_tier = 1
    GROUP BY experiment_id, variant
),
tier2_stats AS (
    SELECT
        experiment_id,
        variant,
        COUNT(DISTINCT user_id) as tier2_attempts,
        COUNT(DISTINCT user_id) FILTER (WHERE completion_status = 'completed') as tier2_completions,
        AVG(time_to_complete_seconds) FILTER (WHERE completion_status = 'completed') as avg_tier2_time
    FROM verification_attempts
    WHERE verification_tier = 2
    GROUP BY experiment_id, variant
)
SELECT
    t1.experiment_id,
    t1.variant,
    t1.tier1_attempts,
    t1.tier1_completions,
    CASE
        WHEN t1.tier1_attempts > 0
        THEN t1.tier1_completions::FLOAT / t1.tier1_attempts
        ELSE 0
    END as tier1_completion_rate,
    t1.avg_tier1_time,
    COALESCE(t2.tier2_attempts, 0) as tier2_attempts,
    COALESCE(t2.tier2_completions, 0) as tier2_completions,
    CASE
        WHEN COALESCE(t2.tier2_attempts, 0) > 0
        THEN t2.tier2_completions::FLOAT / t2.tier2_attempts
        ELSE 0
    END as tier2_completion_rate,
    COALESCE(t2.avg_tier2_time, 0) as avg_tier2_time
FROM tier1_stats t1
LEFT JOIN tier2_stats t2
    ON t1.experiment_id = t2.experiment_id
    AND t1.variant = t2.variant;

-- Index for funnel queries
CREATE INDEX IF NOT EXISTS idx_funnel_metrics
ON verification_funnel_metrics(experiment_id, variant);

-- ============================================================
-- REFRESH COMMANDS
-- Use these to refresh materialized views after data updates
-- ============================================================

-- Refresh all views:
-- REFRESH MATERIALIZED VIEW user_engagement_metrics;
-- REFRESH MATERIALIZED VIEW daily_experiment_metrics;
-- REFRESH MATERIALIZED VIEW verification_funnel_metrics;

-- Concurrent refresh (allows reads during refresh):
-- REFRESH MATERIALIZED VIEW CONCURRENTLY user_engagement_metrics;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY daily_experiment_metrics;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY verification_funnel_metrics;
