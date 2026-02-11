-- Shortlist: Scaffolds Table
-- Phase 3 Migration — Scaffold Generator

-- ============================================================
-- TABLE: scaffolds
-- Stores AI-generated project scaffolds (file tree + contents)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.scaffolds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.capstone_projects(id) ON DELETE SET NULL,
    project_title VARCHAR(200) NOT NULL,
    project_description TEXT NOT NULL,
    tech_stack JSONB NOT NULL DEFAULT '[]'::jsonb,
    include_docker BOOLEAN NOT NULL DEFAULT TRUE,
    include_ci BOOLEAN NOT NULL DEFAULT TRUE,
    include_tests BOOLEAN NOT NULL DEFAULT TRUE,
    files JSONB,
    file_tree TEXT,
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
CREATE INDEX IF NOT EXISTS idx_scaffolds_user_id
    ON public.scaffolds(user_id);
CREATE INDEX IF NOT EXISTS idx_scaffolds_project_id
    ON public.scaffolds(project_id);
CREATE INDEX IF NOT EXISTS idx_scaffolds_status
    ON public.scaffolds(status);
CREATE INDEX IF NOT EXISTS idx_scaffolds_created_at
    ON public.scaffolds(created_at DESC);

-- ============================================================
-- TRIGGER: auto-update updated_at
-- ============================================================
DROP TRIGGER IF EXISTS set_updated_at ON public.scaffolds;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON public.scaffolds
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE public.scaffolds ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own scaffolds" ON public.scaffolds;
CREATE POLICY "Users can view own scaffolds"
    ON public.scaffolds FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own scaffolds" ON public.scaffolds;
CREATE POLICY "Users can insert own scaffolds"
    ON public.scaffolds FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own scaffolds" ON public.scaffolds;
CREATE POLICY "Users can update own scaffolds"
    ON public.scaffolds FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role full access scaffolds" ON public.scaffolds;
CREATE POLICY "Service role full access scaffolds"
    ON public.scaffolds FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');
