"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  api,
  type JDAnalysisResponse,
  type CapstoneResponse,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Code2,
  Target,
  Layers,
  Clock,
  Clipboard,
  Check,
  Trash2,
} from "lucide-react";

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<JDAnalysisResponse | null>(null);
  const [capstone, setCapstone] = useState<CapstoneResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generatingProjects, setGeneratingProjects] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedBullet, setCopiedBullet] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    loadAnalysis();
    loadExistingCapstones();
  }, [id]);

  const loadAnalysis = async () => {
    try {
      const data = await api.getAnalysis(id);
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analysis");
    } finally {
      setLoading(false);
    }
  };

  const loadExistingCapstones = async () => {
    try {
      const data = await api.getCapstoneProjects(id);
      if (data?.projects?.length) {
        setCapstone({
          analysis_id: data.analysis_id,
          projects: data.projects,
          generation_metadata: {
            processing_time_ms: 0,
            projects_generated: data.projects.length,
            projects_persisted: data.projects.length,
          },
        });
      }
    } catch {
      // No existing capstones — that's fine
    }
  };

  const generateProjects = async () => {
    setGeneratingProjects(true);
    setError(null);
    try {
      const data = await api.generateCapstone({ analysis_id: id });
      setCapstone(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate projects"
      );
    } finally {
      setGeneratingProjects(false);
    }
  };

  const copyBullet = async (text: string, index: number) => {
    await navigator.clipboard.writeText(text);
    setCopiedBullet(index);
    setTimeout(() => setCopiedBullet(null), 2000);
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.deleteAnalysis(id);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-6 w-6 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  if (error && !analysis) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <Card>
          <CardContent className="py-8 text-center text-danger">
            {error}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!analysis) return null;

  function tryExtractJSON(text: unknown): Record<string, unknown> | null {
    if (typeof text !== "string" || text.length < 10) return null;
    let clean = text.trim()
      .replace(/^```[a-zA-Z]*\s*/, "")
      .replace(/```\s*$/, "")
      .trim();
    const braceStart = clean.indexOf("{");
    const braceEnd = clean.lastIndexOf("}");
    if (braceStart === -1 || braceEnd <= braceStart) return null;
    try {
      const parsed = JSON.parse(clean.slice(braceStart, braceEnd + 1));
      return typeof parsed === "object" && parsed !== null ? parsed : null;
    } catch { return null; }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let sp: any = null;
  {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let resolved: any = analysis.skill_profile;
    // If it's a string, try to parse
    if (typeof resolved === "string") {
      resolved = tryExtractJSON(resolved) ?? resolved;
    }
    if (typeof resolved === "object" && resolved !== null) {
      // Detect jd_node fallback: skills is empty but summary has the real JSON
      const skills = Array.isArray(resolved.skills) ? resolved.skills : [];
      if (skills.length === 0 && typeof resolved.summary === "string") {
        const embedded = tryExtractJSON(resolved.summary);
        if (embedded && Array.isArray(embedded.skills) && (embedded.skills as unknown[]).length > 0) {
          resolved = embedded;
        }
      }
      sp = resolved;
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let cm: any = null;
  {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let resolved: any = analysis.company_modifiers;
    if (typeof resolved === "string") {
      resolved = tryExtractJSON(resolved) ?? resolved;
    }
    if (typeof resolved === "object" && resolved !== null) {
      cm = resolved;
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 animate-reveal">
        <div className="flex items-center gap-3 sm:gap-4 min-w-0">
          <Button variant="ghost" size="sm" onClick={() => router.back()} className="shrink-0">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="min-w-0">
            <h1 className="text-lg sm:text-2xl font-bold tracking-tight truncate">{analysis.raw_role}</h1>
            <p className="mt-0.5 text-xs sm:text-sm text-secondary">
              {analysis.raw_company_type.replace("_", " ")} company
              {analysis.raw_geography && ` \u00b7 ${analysis.raw_geography}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {confirmDelete ? (
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-danger/30 bg-danger-dim px-3 py-1.5">
              <span className="text-xs text-danger">Delete?</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDelete}
                loading={deleting}
                className="text-danger hover:bg-danger/10 h-7 px-2 text-xs"
              >
                Yes, delete
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setConfirmDelete(false)}
                className="h-7 px-2 text-xs"
              >
                Cancel
              </Button>
            </div>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setConfirmDelete(true)}
              className="text-muted hover:text-danger hover:bg-danger/5"
              title="Delete analysis"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
          <Button
            onClick={generateProjects}
            loading={generatingProjects}
          >
          <Code2 className="h-4 w-4" />
          {capstone
            ? "Regenerate Capstone Projects"
            : generatingProjects
              ? "Generating..."
              : "Generate Capstone Projects"}
        </Button>
        </div>
      </div>

      {sp ? (() => {
        const hasSkills = Array.isArray(sp.skills) && sp.skills.length > 0;
        const hasResponsibilities = Array.isArray(sp.key_responsibilities) && sp.key_responsibilities.length > 0;
        const hasExpectations = Array.isArray(sp.engineering_expectations) && sp.engineering_expectations.length > 0;
        const hasSummary = sp.summary && typeof sp.summary === "string" &&
          !sp.summary.trim().startsWith("{") &&
          !sp.summary.trim().startsWith("```") &&
          !sp.summary.includes('"skills"') &&
          sp.summary.trim().length > 3;
        const isEmpty = !hasSkills && !hasResponsibilities && !hasExpectations && !hasSummary;

        return (
          <Card className="animate-reveal d1 overflow-hidden">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 border border-accent/10">
                    <Target className="h-4 w-4 text-accent" />
                  </div>
                  Skill Profile
                </CardTitle>
                <div className="flex items-center gap-2">
                  {String(sp.experience_level || "") !== "mid" && (
                    <Badge variant="accent" className="text-[11px]">{String(sp.experience_level)}</Badge>
                  )}
                  {String(sp.domain || "") !== "Software Engineering" && String(sp.domain || "") !== analysis.raw_role && (
                    <Badge className="text-[11px]">{String(sp.domain)}</Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Empty state — prompt to re-analyze */}
              {isEmpty && (
                <div className="flex flex-col items-center justify-center py-6 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-warning/10 border border-warning/20 mb-3">
                    <Target className="h-5 w-5 text-warning" />
                  </div>
                  <p className="text-sm font-medium text-primary mb-1">Skill extraction incomplete</p>
                  <p className="text-xs text-muted max-w-md">
                    The AI couldn&apos;t fully parse this JD. Delete this analysis and re-analyze to get a complete skill profile.
                  </p>
                </div>
              )}

              {/* Summary */}
              {hasSummary && (
                <p className="text-[13px] leading-relaxed text-secondary border-l-2 border-accent/20 pl-4">
                  {String(sp.summary)}
                </p>
              )}

              {/* Skills by source */}
              {hasSkills && (() => {
                const grouped: Record<string, Array<{ name: string; category: string; weight: number; source: string }>> = {};
                sp.skills.forEach((s: { name: string; category: string; weight: number; source: string }) => {
                  const key = s.source || "inferred";
                  if (!grouped[key]) grouped[key] = [];
                  grouped[key].push(s);
                });
                const sections = [
                  { key: "required", label: "Required", dot: "bg-accent" },
                  { key: "preferred", label: "Preferred", dot: "bg-info" },
                  { key: "inferred", label: "Inferred", dot: "bg-secondary/50" },
                ].filter(s => grouped[s.key]?.length);

                return (
                  <div className="space-y-5">
                    {sections.map(({ key, label, dot }) => {
                      const skills = grouped[key].sort((a, b) => b.weight - a.weight);
                      return (
                        <div key={key}>
                          <div className="flex items-center gap-2 mb-3">
                            <span className={`h-2 w-2 rounded-full ${dot}`} />
                            <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-muted/70">{label}</span>
                            <span className="h-px flex-1 bg-edge/40" />
                            <span className="text-[10px] text-accent/70 font-mono">{skills.length}</span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {skills.map((skill, idx) => (
                              <div
                                key={idx}
                                className="group flex items-center gap-2 rounded-lg border border-edge/50 bg-surface/40 px-3 py-2 transition-all hover:border-accent/15 hover:bg-surface/60"
                              >
                                <span className="text-[12.5px] font-medium text-primary">{skill.name}</span>
                                <span className="flex items-center gap-1">
                                  <span className="h-1 rounded-full bg-edge/60 overflow-hidden w-10">
                                    <span
                                      className={`block h-full rounded-full ${key === "required" ? "bg-accent/60" : key === "preferred" ? "bg-info/60" : "bg-secondary/40"}`}
                                      style={{ width: `${(skill.weight / 10) * 100}%` }}
                                    />
                                  </span>
                                  <span className="text-[10px] text-accent/70 font-mono tabular-nums">{skill.weight.toFixed(1)}</span>
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                );
              })()}

              {/* Key Responsibilities */}
              {hasResponsibilities && (
                <div className={hasSkills ? "border-t border-edge/30 pt-5" : ""}>
                  <h4 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-muted/70">
                    <span className="h-px flex-1 bg-edge/40" />
                    Key Responsibilities
                    <span className="h-px flex-1 bg-edge/40" />
                  </h4>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {sp.key_responsibilities.map((r: string, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2.5 rounded-lg border border-edge/30 bg-surface/20 px-3 py-2.5"
                      >
                        <span className="mt-[6px] h-1.5 w-1.5 shrink-0 rounded-full bg-accent/30" />
                        <span className="text-[12.5px] leading-relaxed text-secondary">
                          {typeof r === "string" ? r : String(r)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Engineering Expectations */}
              {hasExpectations && (
                <div className={(hasSkills || hasResponsibilities) ? "border-t border-edge/30 pt-5" : ""}>
                  <h4 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-muted/70">
                    <span className="h-px flex-1 bg-transparent" />
                    Engineering Expectations
                    <span className="h-px flex-1 bg-edge/40" />
                  </h4>
                  <div className="space-y-3">
                    {[...sp.engineering_expectations]
                      .sort((a: { importance: number }, b: { importance: number }) => b.importance - a.importance)
                      .map((exp: { dimension: string; importance: number; description: string }, idx: number) => (
                        <div key={idx} className="rounded-lg border border-edge/30 bg-surface/20 p-3.5">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-[13px] font-semibold text-primary">{exp.dimension}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 rounded-full bg-edge/40 overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-accent/60 transition-all duration-500"
                                  style={{ width: `${(exp.importance / 10) * 100}%` }}
                                />
                              </div>
                              <span className="font-mono text-[10px] text-accent/70 tabular-nums w-5 text-right">
                                {exp.importance.toFixed(1)}
                              </span>
                            </div>
                          </div>
                          <p className="text-[12px] leading-relaxed text-secondary/70">
                            {typeof exp.description === "string" ? exp.description : String(exp.description)}
                          </p>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })() : (
        <Card className="animate-reveal d1">
          <CardContent className="py-8 text-center text-muted">
            Skill profile data unavailable
          </CardContent>
        </Card>
      )}

      {cm && (
        <Card className="animate-reveal d2">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-info/10 border border-info/10">
                <Layers className="h-4 w-4 text-info" />
              </div>
              Company Intelligence
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Portfolio Focus */}
            {cm.portfolio_focus && typeof cm.portfolio_focus === "string" && cm.portfolio_focus.trim().length > 0 && (
              <p className="text-[13px] leading-relaxed text-secondary border-l-2 border-info/20 pl-4">
                {cm.portfolio_focus}
              </p>
            )}

            {/* Emphasis Areas */}
            {Array.isArray(cm.emphasis_areas) && cm.emphasis_areas.length > 0 && (
              <div>
                <h4 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-muted/70">
                  <span className="h-1.5 w-1.5 rounded-full bg-info/50" />
                  Emphasis Areas
                  <span className="h-px flex-1 bg-edge/40" />
                </h4>
                <div className="flex flex-wrap gap-2">
                  {cm.emphasis_areas.map((area: string, idx: number) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-2 rounded-lg border border-info/15 bg-info/[0.04] px-3.5 py-2 text-[12.5px] font-medium text-primary transition hover:border-info/30 hover:bg-info/[0.07]"
                    >
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-info/60" />
                      {typeof area === "string" ? area : String(area)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Weight Adjustments */}
            {cm.weight_adjustments && typeof cm.weight_adjustments === "object" && Object.keys(cm.weight_adjustments).length > 0 && (
              <div>
                <h4 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[0.14em] text-muted/70">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent/50" />
                  Skill Weight Adjustments
                  <span className="h-px flex-1 bg-edge/40" />
                </h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(cm.weight_adjustments).map(([skill, adj]: [string, unknown], idx: number) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-edge/40 bg-surface/30 px-3 py-1.5 text-[12px] font-medium text-secondary"
                    >
                      {skill}
                      <span className={`font-mono text-[11px] ${Number(adj) > 0 ? "text-ok" : Number(adj) < 0 ? "text-danger" : "text-muted"}`}>
                        {Number(adj) > 0 ? "+" : ""}{Number(adj).toFixed(1)}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-danger/30 bg-danger-dim px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {/* Generated Projects */}
      {capstone && capstone.projects.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between animate-reveal">
            <h2 className="text-xl font-bold tracking-tight">
              Generated Capstone Projects
            </h2>
            <span className="text-sm text-muted font-mono">
              <Clock className="inline h-3 w-3 mr-1" />
              {(capstone.generation_metadata.processing_time_ms / 1000).toFixed(1)}s
            </span>
          </div>

          {capstone.projects.map((project, i) => (
            <Card key={i} className={`overflow-hidden animate-reveal d${Math.min(i + 1, 8)}`}>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <CardTitle>{project.title}</CardTitle>
                    <CardDescription className="mt-2">
                      {project.problem_statement}
                    </CardDescription>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge variant="accent" className="whitespace-nowrap">
                      {project.complexity_level}/5
                    </Badge>
                    <Badge className="whitespace-nowrap">
                      ~{project.estimated_days}d
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Tech Stack */}
                <div>
                  <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted">
                    Tech Stack
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {project.tech_stack.map((tech, j) => (
                      <Badge key={j}>{tech}</Badge>
                    ))}
                  </div>
                </div>

                {/* Architecture */}
                {project.architecture && (
                  <div>
                    <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted">
                      Architecture
                    </h4>
                    {project.architecture.description && (
                      <p className="text-sm text-secondary mb-3">
                        {project.architecture.description}
                      </p>
                    )}
                    {Array.isArray(project.architecture.components) && project.architecture.components.length > 0 && (
                      <div className="mb-3">
                        <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted/60 block mb-2">Components</span>
                        <div className="flex flex-wrap gap-1.5">
                          {project.architecture.components.map((comp, j) => (
                            <span
                              key={j}
                              className="inline-flex items-center rounded-md border border-edge/40 bg-surface/30 px-2.5 py-1 text-[12px] text-secondary"
                            >
                              {comp}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {project.architecture.data_flow && (
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-[0.12em] text-muted/60 block mb-1.5">Data Flow</span>
                        <p className="text-[12.5px] leading-relaxed text-secondary/80 border-l-2 border-accent/15 pl-3">
                          {project.architecture.data_flow}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Key Features */}
                {project.key_features.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-muted">
                      Key Features
                    </h4>
                    <ul className="list-inside list-disc space-y-1 text-sm text-secondary">
                      {project.key_features.map((f, j) => (
                        <li key={j}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Resume Bullet */}
                <div className="flex items-start gap-2 rounded-lg border border-edge bg-well p-3">
                  <div className="flex-1">
                    <h4 className="mb-1 text-xs font-medium uppercase tracking-wider text-muted">
                      Resume Bullet
                    </h4>
                    <p className="text-sm text-primary">
                      {project.resume_bullet}
                    </p>
                  </div>
                  <button
                    onClick={() => copyBullet(project.resume_bullet, i)}
                    className="rounded p-1.5 text-muted transition hover:bg-raised hover:text-primary"
                    title="Copy to clipboard"
                  >
                    {copiedBullet === i ? (
                      <Check className="h-4 w-4 text-ok" />
                    ) : (
                      <Clipboard className="h-4 w-4" />
                    )}
                  </button>
                </div>

                {/* Differentiator */}
                <div className="rounded-lg border border-ok/20 bg-ok-dim p-3">
                  <h4 className="mb-1 text-xs font-medium uppercase tracking-wider text-ok">
                    What Makes This Stand Out
                  </h4>
                  <p className="text-sm text-secondary">
                    {project.differentiator}
                  </p>
                </div>

                {/* Recruiter Match */}
                <div className="rounded-lg border border-info/20 bg-info-dim p-3">
                  <h4 className="mb-1 text-xs font-medium uppercase tracking-wider text-info">
                    Recruiter Match Reasoning
                  </h4>
                  <p className="text-sm text-secondary">
                    {project.recruiter_match_reasoning}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
