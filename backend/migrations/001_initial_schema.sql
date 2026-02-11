-- Shortlist: Initial Database Schema
-- Phase 1 Migration

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: jd_analyses
-- Stores JD input text & AI-extracted analysis results
-- ============================================================
CREATE TABLE IF NOT EXISTS public.jd_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    jd_text TEXT NOT NULL CHECK (char_length(jd_text) BETWEEN 50 AND 15000),
    role VARCHAR(200) NOT NULL,
    company_type VARCHAR(50) NOT NULL CHECK (company_type IN ('startup', 'mid_level', 'faang', 'research', 'enterprise')),
    geography VARCHAR(100),
    skill_profile JSONB,
    engineering_expectations JSONB,
    company_modifiers JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: capstone_projects
-- Stores AI-generated capstone projects linked to an analysis
-- ============================================================
CREATE TABLE IF NOT EXISTS public.capstone_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    analysis_id UUID NOT NULL REFERENCES public.jd_analyses(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    problem_statement TEXT NOT NULL,
    architecture TEXT,
    tech_stack JSONB NOT NULL DEFAULT '[]'::jsonb,
    complexity INTEGER NOT NULL CHECK (complexity BETWEEN 1 AND 5),
    resume_bullet TEXT,
    differentiator TEXT,
    is_selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLE: repo_analyses  (Phase 2 placeholder)
-- Stores GitHub repo analysis results
-- ============================================================
CREATE TABLE IF NOT EXISTS public.repo_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    github_url VARCHAR(500) NOT NULL,
    scorecard JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_jd_analyses_user_id ON public.jd_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_jd_analyses_status ON public.jd_analyses(status);
CREATE INDEX IF NOT EXISTS idx_jd_analyses_created_at ON public.jd_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_capstone_projects_user_id ON public.capstone_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_capstone_projects_analysis_id ON public.capstone_projects(analysis_id);
CREATE INDEX IF NOT EXISTS idx_repo_analyses_user_id ON public.repo_analyses(user_id);

-- ============================================================
-- TRIGGER: auto-update updated_at on jd_analyses
-- ============================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON public.jd_analyses;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON public.jd_analyses
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Users can only see/modify their own records
-- Service role bypasses RLS
-- ============================================================

-- jd_analyses RLS
ALTER TABLE public.jd_analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own JD analyses" ON public.jd_analyses;
CREATE POLICY "Users can view own JD analyses"
    ON public.jd_analyses FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own JD analyses" ON public.jd_analyses;
CREATE POLICY "Users can insert own JD analyses"
    ON public.jd_analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own JD analyses" ON public.jd_analyses;
CREATE POLICY "Users can update own JD analyses"
    ON public.jd_analyses FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access jd_analyses" ON public.jd_analyses;
CREATE POLICY "Service role full access jd_analyses"
    ON public.jd_analyses FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- capstone_projects RLS
ALTER TABLE public.capstone_projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own capstone projects" ON public.capstone_projects;
CREATE POLICY "Users can view own capstone projects"
    ON public.capstone_projects FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own capstone projects" ON public.capstone_projects;
CREATE POLICY "Users can insert own capstone projects"
    ON public.capstone_projects FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own capstone projects" ON public.capstone_projects;
CREATE POLICY "Users can update own capstone projects"
    ON public.capstone_projects FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access capstone_projects" ON public.capstone_projects;
CREATE POLICY "Service role full access capstone_projects"
    ON public.capstone_projects FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- repo_analyses RLS
ALTER TABLE public.repo_analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own repo analyses" ON public.repo_analyses;
CREATE POLICY "Users can view own repo analyses"
    ON public.repo_analyses FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own repo analyses" ON public.repo_analyses;
CREATE POLICY "Users can insert own repo analyses"
    ON public.repo_analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access repo_analyses" ON public.repo_analyses;
CREATE POLICY "Service role full access repo_analyses"
    ON public.repo_analyses FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
