-- v0.7.0 Migration Script
-- Adds cost tracking and token usage fields to llm_logs
-- Creates llm_model_pricing table for model pricing configuration

BEGIN;

-- ============================================================================
-- 1. Modify llm_logs table - Add token usage and cost tracking fields
-- ============================================================================

ALTER TABLE llm_logs
ADD COLUMN IF NOT EXISTS input_tokens INTEGER,
ADD COLUMN IF NOT EXISTS output_tokens INTEGER,
ADD COLUMN IF NOT EXISTS total_tokens INTEGER,
ADD COLUMN IF NOT EXISTS cached_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS reasoning_tokens INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS cost_input_usd DECIMAL(10, 6),
ADD COLUMN IF NOT EXISTS cost_output_usd DECIMAL(10, 6),
ADD COLUMN IF NOT EXISTS cost_total_usd DECIMAL(10, 6);

-- Add index for cost-based queries
CREATE INDEX IF NOT EXISTS idx_llm_logs_cost_total ON llm_logs(cost_total_usd DESC);
CREATE INDEX IF NOT EXISTS idx_llm_logs_model_created ON llm_logs(model_version, created_at DESC);

-- ============================================================================
-- 2. Create llm_model_pricing table
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_model_pricing (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(128) UNIQUE NOT NULL,
    provider VARCHAR(64) NOT NULL,

    -- Pricing information (USD per 1M tokens)
    price_input_per_1m DECIMAL(10, 4) NOT NULL,
    price_output_per_1m DECIMAL(10, 4) NOT NULL,
    price_cached_per_1m DECIMAL(10, 4) DEFAULT 0,

    -- Model specifications
    context_window INTEGER,
    max_output_tokens INTEGER,

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Description and tags
    description TEXT,
    tags VARCHAR(64)[]
);

-- Create index for model lookup
CREATE INDEX IF NOT EXISTS idx_model_pricing_active ON llm_model_pricing(model_name) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_model_pricing_provider ON llm_model_pricing(provider);

-- ============================================================================
-- 3. Insert initial pricing data (2026 pricing)
-- ============================================================================

-- OpenAI GPT-5 family
INSERT INTO llm_model_pricing (model_name, provider, price_input_per_1m, price_output_per_1m, context_window, description, tags)
VALUES
    ('gpt-5', 'openai', 1.25, 10.00, 400000, 'GPT-5 flagship model with advanced reasoning capabilities', ARRAY['chat', 'reasoning', 'flagship']),
    ('gpt-5-mini', 'openai', 0.25, 2.00, 400000, 'Cost-efficient GPT-5 variant, optimized for speed and value', ARRAY['chat', 'fast', 'cost-effective']),
    ('gpt-5-nano', 'openai', 0.05, 0.40, 200000, 'Ultra-lightweight GPT-5 for simple tasks', ARRAY['chat', 'lightweight', 'budget'])
ON CONFLICT (model_name) DO UPDATE SET
    price_input_per_1m = EXCLUDED.price_input_per_1m,
    price_output_per_1m = EXCLUDED.price_output_per_1m,
    context_window = EXCLUDED.context_window,
    description = EXCLUDED.description,
    updated_at = NOW();

-- OpenAI GPT-4o family
INSERT INTO llm_model_pricing (model_name, provider, price_input_per_1m, price_output_per_1m, context_window, description, tags)
VALUES
    ('gpt-4o', 'openai', 2.50, 10.00, 128000, 'GPT-4 optimized for speed and performance', ARRAY['chat', 'previous-gen']),
    ('gpt-4o-mini', 'openai', 0.15, 0.60, 128000, 'Compact and efficient GPT-4o variant', ARRAY['chat', 'cost-effective', 'previous-gen'])
ON CONFLICT (model_name) DO UPDATE SET
    price_input_per_1m = EXCLUDED.price_input_per_1m,
    price_output_per_1m = EXCLUDED.price_output_per_1m,
    context_window = EXCLUDED.context_window,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Anthropic Claude family
INSERT INTO llm_model_pricing (model_name, provider, price_input_per_1m, price_output_per_1m, context_window, description, tags)
VALUES
    ('claude-sonnet-4', 'anthropic', 0.30, 1.50, 200000, 'Claude Sonnet 4 - balanced performance and cost', ARRAY['chat', 'anthropic', 'balanced']),
    ('claude-haiku-4', 'anthropic', 0.25, 1.25, 200000, 'Claude Haiku 4 - fast and affordable', ARRAY['chat', 'anthropic', 'fast'])
ON CONFLICT (model_name) DO UPDATE SET
    price_input_per_1m = EXCLUDED.price_input_per_1m,
    price_output_per_1m = EXCLUDED.price_output_per_1m,
    context_window = EXCLUDED.context_window,
    description = EXCLUDED.description,
    updated_at = NOW();

-- ============================================================================
-- 4. Create helper function for cost calculation (optional, for DB-side calcs)
-- ============================================================================

CREATE OR REPLACE FUNCTION calculate_llm_cost(
    p_input_tokens INTEGER,
    p_output_tokens INTEGER,
    p_cached_tokens INTEGER,
    p_price_input_per_1m DECIMAL,
    p_price_output_per_1m DECIMAL,
    p_price_cached_per_1m DECIMAL
)
RETURNS TABLE(
    cost_input DECIMAL(10, 6),
    cost_output DECIMAL(10, 6),
    cost_total DECIMAL(10, 6)
) AS $$
DECLARE
    v_uncached_tokens INTEGER;
    v_cost_input DECIMAL(10, 6);
    v_cost_output DECIMAL(10, 6);
BEGIN
    -- Calculate uncached input tokens
    v_uncached_tokens := p_input_tokens - COALESCE(p_cached_tokens, 0);

    -- Calculate input cost (uncached + cached)
    v_cost_input := (v_uncached_tokens * p_price_input_per_1m / 1000000.0) +
                    (COALESCE(p_cached_tokens, 0) * COALESCE(p_price_cached_per_1m, 0) / 1000000.0);

    -- Calculate output cost
    v_cost_output := p_output_tokens * p_price_output_per_1m / 1000000.0;

    -- Return results
    RETURN QUERY SELECT v_cost_input, v_cost_output, v_cost_input + v_cost_output;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 5. Create view for cost analytics (optional)
-- ============================================================================

CREATE OR REPLACE VIEW v_cost_summary AS
SELECT
    DATE(l.created_at) AS summary_date,
    l.model_version,
    l.user_id,
    COUNT(*) AS total_requests,
    SUM(l.input_tokens) AS total_input_tokens,
    SUM(l.output_tokens) AS total_output_tokens,
    SUM(l.cost_total_usd) AS total_cost_usd,
    AVG(l.cost_total_usd) AS avg_cost_per_request,
    AVG(l.latency_ms) AS avg_latency_ms
FROM llm_logs l
WHERE l.status = 'success'
  AND l.cost_total_usd IS NOT NULL
GROUP BY DATE(l.created_at), l.model_version, l.user_id;

COMMIT;

-- ============================================================================
-- Migration completed successfully
-- ============================================================================

-- Verification queries (run separately if needed):
-- SELECT COUNT(*) FROM llm_model_pricing;
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'llm_logs' AND column_name LIKE '%token%' OR column_name LIKE '%cost%';
