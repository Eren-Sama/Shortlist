-- Shortlist: Resume Fitness Scorer + Avatars Storage
-- Migration 004

-- ============================================================
-- TABLE: resume_fitness_scores
-- Stores AI-evaluated resume-to-JD fitness scores
-- ============================================================
CREATE TABLE IF NOT EXISTS public.resume_fitness_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    analysis_id UUID NOT NULL REFERENCES public.jd_analyses(id) ON DELETE CASCADE,
    resume_text TEXT NOT NULL,
    fitness_score DECIMAL(5, 2),
    verdict TEXT CHECK (verdict IN ('strong_fit', 'good_fit', 'partial_fit', 'weak_fit')),
    matched_skills JSONB DEFAULT '[]'::jsonb,
    missing_skills JSONB DEFAULT '[]'::jsonb,
    strengths JSONB DEFAULT '[]'::jsonb,
    improvements JSONB DEFAULT '[]'::jsonb,
    detailed_feedback TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_fitness_user_id ON public.resume_fitness_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_fitness_analysis_id ON public.resume_fitness_scores(analysis_id);
CREATE INDEX IF NOT EXISTS idx_fitness_created_at ON public.resume_fitness_scores(created_at DESC);

-- RLS
ALTER TABLE public.resume_fitness_scores ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own fitness scores"
    ON public.resume_fitness_scores
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own fitness scores"
    ON public.resume_fitness_scores
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own fitness scores"
    ON public.resume_fitness_scores
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Auto-update updated_at (reuse existing trigger function if available)
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_fitness_updated_at
    BEFORE UPDATE ON public.resume_fitness_scores
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- ============================================================
-- STORAGE: avatars bucket for profile pictures
-- ============================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT (id) DO NOTHING;

-- Anyone can view avatars (public bucket)
CREATE POLICY "Public avatar access"
    ON storage.objects
    FOR SELECT
    USING (bucket_id = 'avatars');

-- Authenticated users can upload their own avatars
CREATE POLICY "Users can upload own avatar"
    ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'avatars'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can update/replace their own avatars
CREATE POLICY "Users can update own avatar"
    ON storage.objects
    FOR UPDATE
    USING (
        bucket_id = 'avatars'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can delete their own avatars
CREATE POLICY "Users can delete own avatar"
    ON storage.objects
    FOR DELETE
    USING (
        bucket_id = 'avatars'
        AND auth.uid()::text = (storage.foldername(name))[1]
    );
