/** Typed fetch wrapper for the FastAPI backend. All requests include the Supabase JWT. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiError {
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const error: ApiError = await res.json().catch(() => ({
        detail: `Request failed with status ${res.status}`,
      }));
      throw new Error(error.detail || "An unknown error occurred");
    }

    return res.json();
  }

  async analyzeJD(data: {
    jd_text: string;
    role: string;
    company_type: string;
    geography?: string;
  }) {
    return this.request<JDAnalysisResponse>("POST", "/api/v1/jd/analyze", data);
  }

  async getAnalysis(analysisId: string) {
    return this.request<JDAnalysisResponse>("GET", `/api/v1/jd/${analysisId}`);
  }

  async listAnalyses(limit = 20, offset = 0) {
    return this.request<AnalysisListResponse>(
      "GET",
      `/api/v1/jd/?limit=${limit}&offset=${offset}`
    );
  }

  async deleteAnalysis(analysisId: string) {
    return this.request<{ deleted: boolean; analysis_id: string }>(
      "DELETE",
      `/api/v1/jd/${analysisId}`
    );
  }

  async generateCapstone(data: {
    analysis_id: string;
    num_projects?: number;
    preferred_stack?: string[];
  }) {
    return this.request<CapstoneResponse>(
      "POST",
      "/api/v1/capstone/generate",
      data
    );
  }

  async getCapstoneProjects(analysisId: string) {
    return this.request<{ analysis_id: string; projects: CapstoneProject[] }>(
      "GET",
      `/api/v1/capstone/${analysisId}`
    );
  }

  async toggleProjectSelection(projectId: string, selected: boolean) {
    return this.request<{ id: string; is_selected: boolean }>(
      "PUT",
      `/api/v1/capstone/${projectId}/select?selected=${selected}`
    );
  }

  async analyzeRepo(data: { github_url: string }) {
    return this.request<RepoAnalysisResponse>(
      "POST",
      "/api/v1/repo/analyze",
      data
    );
  }

  async getRepoAnalysis(analysisId: string) {
    return this.request<RepoAnalysisResponse>(
      "GET",
      `/api/v1/repo/${analysisId}`
    );
  }

  async listRepoAnalyses(limit = 20, offset = 0) {
    return this.request<RepoAnalysisListResponse>(
      "GET",
      `/api/v1/repo/?limit=${limit}&offset=${offset}`
    );
  }

  async generateScaffold(data: {
    project_title: string;
    project_description: string;
    tech_stack: string[];
    include_docker?: boolean;
    include_ci?: boolean;
    include_tests?: boolean;
    analysis_id?: string;
    project_id?: string;
  }) {
    return this.request<ScaffoldResponse>(
      "POST",
      "/api/v1/scaffold/generate",
      data
    );
  }

  async getScaffold(scaffoldId: string) {
    return this.request<ScaffoldResponse>(
      "GET",
      `/api/v1/scaffold/${scaffoldId}`
    );
  }

  async listScaffolds(limit = 20, offset = 0) {
    return this.request<ScaffoldListResponse>(
      "GET",
      `/api/v1/scaffold/?limit=${limit}&offset=${offset}`
    );
  }

  async optimizePortfolio(data: {
    project_title: string;
    project_description: string;
    tech_stack: string[];
    key_features?: string[];
    repo_score?: number;
    target_role?: string;
    analysis_id?: string;
  }) {
    return this.request<PortfolioResponse>(
      "POST",
      "/api/v1/portfolio/optimize",
      data
    );
  }

  async getPortfolio(portfolioId: string) {
    return this.request<PortfolioRecord>(
      "GET",
      `/api/v1/portfolio/${portfolioId}`
    );
  }

  async listPortfolios(limit = 20, offset = 0) {
    return this.request<PortfolioListResponse>(
      "GET",
      `/api/v1/portfolio/?limit=${limit}&offset=${offset}`
    );
  }

  async scoreFitness(data: { analysis_id: string; resume_text: string }) {
    return this.request<FitnessScoreResponse>(
      "POST",
      "/api/v1/fitness/score",
      data
    );
  }

  async getFitness(fitnessId: string) {
    return this.request<FitnessScoreResponse>(
      "GET",
      `/api/v1/fitness/${fitnessId}`
    );
  }

  async listFitnessScores(limit = 20, offset = 0) {
    return this.request<FitnessListResponse>(
      "GET",
      `/api/v1/fitness/?limit=${limit}&offset=${offset}`
    );
  }
}


export interface Skill {
  name: string;
  category: string;
  weight: number;
  source: string;
}

export interface EngineeringExpectation {
  dimension: string;
  importance: number;
  description: string;
}

export interface SkillProfile {
  skills: Skill[];
  experience_level: string;
  domain: string;
  engineering_expectations: EngineeringExpectation[];
  key_responsibilities: string[];
  summary: string;
}

export interface CompanyModifiers {
  company_type: string;
  emphasis_areas: string[];
  weight_adjustments: Record<string, number>;
  portfolio_focus: string;
}

export interface JDAnalysisResponse {
  analysis_id: string;
  skill_profile: SkillProfile;
  company_modifiers: CompanyModifiers;
  raw_role: string;
  raw_company_type: string;
  raw_geography?: string;
}

export interface AnalysisListItem {
  id: string;
  role: string;
  company_type: string;
  geography?: string;
  status: string;
  processing_time_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface AnalysisListResponse {
  analyses: AnalysisListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ArchitectureOverview {
  description: string;
  components: string[];
  data_flow: string;
  diagram_mermaid?: string;
}

export interface CapstoneProject {
  title: string;
  problem_statement: string;
  recruiter_match_reasoning: string;
  architecture: ArchitectureOverview;
  tech_stack: string[];
  complexity_level: number;
  estimated_days: number;
  resume_bullet: string;
  key_features: string[];
  differentiator: string;
}

export interface CapstoneResponse {
  analysis_id: string;
  projects: CapstoneProject[];
  generation_metadata: {
    processing_time_ms: number;
    projects_generated: number;
    projects_persisted: number;
  };
}


export interface ScoreDimension {
  name: string;
  score: number;
  details: string;
  suggestions: string[];
}

export interface RepoScoreCard {
  repo_url: string;
  repo_name: string;
  primary_language?: string;
  total_files: number;
  total_lines: number;
  code_quality: ScoreDimension;
  test_coverage: ScoreDimension;
  complexity: ScoreDimension;
  structure: ScoreDimension;
  deployment_readiness: ScoreDimension;
  overall_score: number;
  summary: string;
  top_improvements: string[];
}

export interface RepoAnalysisResponse {
  analysis_id: string;
  scorecard: RepoScoreCard;
  analysis_metadata: Record<string, unknown>;
}

export interface RepoAnalysisListItem {
  id: string;
  github_url: string;
  repo_name?: string;
  primary_language?: string;
  overall_score?: number;
  status: string;
  processing_time_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface RepoAnalysisListResponse {
  analyses: RepoAnalysisListItem[];
  total: number;
  limit: number;
  offset: number;
}


export interface GeneratedFile {
  path: string;
  content: string;
  language: string;
  description: string;
}

export interface ScaffoldResponse {
  project_name: string;
  files: GeneratedFile[];
  file_tree: string;
  download_url?: string;
  generation_metadata: Record<string, unknown>;
}

export interface ScaffoldListItem {
  id: string;
  project_id?: string;
  project_title: string;
  tech_stack: string[];
  status: string;
  processing_time_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface ScaffoldListResponse {
  scaffolds: ScaffoldListItem[];
  total: number;
  limit: number;
  offset: number;
}


export interface ResumeBullet {
  bullet: string;
  keywords: string[];
  impact_type: "quantitative" | "qualitative" | "technical";
}

export interface DemoStep {
  timestamp: string;
  action: string;
  narration: string;
}

export interface DemoScript {
  total_duration_seconds: number;
  opening_hook: string;
  steps: DemoStep[];
  closing_cta: string;
}

export interface LinkedInPost {
  hook: string;
  body: string;
  hashtags: string[];
  call_to_action: string;
}

export interface PortfolioResponse {
  readme_markdown: string;
  resume_bullets: ResumeBullet[];
  demo_script: DemoScript;
  linkedin_post: LinkedInPost;
  generation_metadata: {
    portfolio_id: string;
    processing_time_ms: number;
    model: string;
  };
}

export interface PortfolioRecord {
  id: string;
  project_title: string;
  project_description: string;
  tech_stack: string[];
  target_role?: string;
  readme_markdown?: string;
  resume_bullets?: ResumeBullet[];
  demo_script?: DemoScript;
  linkedin_post?: LinkedInPost;
  status: string;
  processing_time_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioListItem {
  id: string;
  project_title: string;
  tech_stack: string[];
  target_role?: string;
  status: string;
  processing_time_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioListResponse {
  items: PortfolioListItem[];
  total: number;
  limit: number;
  offset: number;
}


export interface MatchedSkill {
  skill: string;
  evidence: string;
  strength: "strong" | "moderate" | "weak";
}

export interface MissingSkill {
  skill: string;
  importance: "critical" | "important" | "nice_to_have";
  suggestion: string;
}

export interface Improvement {
  area: string;
  current_state: string;
  recommended_action: string;
  impact: "high" | "medium" | "low";
}

export interface FitnessScoreResponse {
  fitness_id: string;
  analysis_id: string;
  fitness_score: number;
  verdict: "strong_fit" | "good_fit" | "partial_fit" | "weak_fit";
  matched_skills: MatchedSkill[];
  missing_skills: MissingSkill[];
  strengths: string[];
  improvements: Improvement[];
  detailed_feedback: string;
  processing_time_ms?: number;
}

export interface FitnessListItem {
  id: string;
  analysis_id: string;
  fitness_score: number;
  verdict: string;
  status: string;
  processing_time_ms?: number;
  created_at: string;
  updated_at: string;
}

export interface FitnessListResponse {
  scores: FitnessListItem[];
  total: number;
  limit: number;
  offset: number;
}

export const api = new ApiClient();
