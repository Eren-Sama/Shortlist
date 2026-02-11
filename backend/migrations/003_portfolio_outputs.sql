-- Shortlist: Portfolio Outputs Table
-- Phase 4 Migration — Portfolio Optimizer

-- ============================================================
-- TABLE: portfolio_outputs
-- Stores AI-generated portfolio materials (README, bullets, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.portfolio_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_title VARCHAR(200) NOT NULL,
    project_description TEXT NOT NULL,
    tech_stack JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_role VARCHAR(200),
    analysis_id UUID REFERENCES public.jd_analyses(id) ON DELETE SET NULL,
    readme_markdown TEXT,
    resume_bullets JSONB,
    demo_script JSONB,
    linkedin_post JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_portfolio_outputs_user_id
    ON public.portfolio_outputs(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_outputs_analysis_id
    ON public.portfolio_outputs(analysis_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_outputs_status
    ON public.portfolio_outputs(status);
CREATE INDEX IF NOT EXISTS idx_portfolio_outputs_created_at
    ON public.portfolio_outputs(created_at DESC);

-- ============================================================
-- TRIGGER: auto-update updated_at
-- ============================================================
DROP TRIGGER IF EXISTS set_updated_at ON public.portfolio_outputs;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON public.portfolio_outputs
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE public.portfolio_outputs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own portfolio outputs" ON public.portfolio_outputs;
CREATE POLICY "Users can view own portfolio outputs"
    ON public.portfolio_outputs FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own portfolio outputs" ON public.portfolio_outputs;
CREATE POLICY "Users can insert own portfolio outputs"
    ON public.portfolio_outputs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own portfolio outputs" ON public.portfolio_outputs;
CREATE POLICY "Users can update own portfolio outputs"
    ON public.portfolio_outputs FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access portfolio_outputs" ON public.portfolio_outputs;
CREATE POLICY "Service role full access portfolio_outputs"
    ON public.portfolio_outputs FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
