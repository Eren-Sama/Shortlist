"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import type {
  FitnessScoreResponse,
  FitnessListItem,
  AnalysisListItem,
} from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Upload,
  Clock,
  ChevronRight,
  ChevronDown,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Target,
  Loader2,
  ArrowLeft,
  Sparkles,
  File as FileIcon,
  X,
  Briefcase,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";

const verdictConfig: Record<
  string,
  { label: string; color: string; bg: string; border: string; icon: typeof CheckCircle2 }
> = {
  strong_fit: {
    label: "Strong Fit",
    color: "text-ok",
    bg: "bg-ok/10",
    border: "border-ok/30",
    icon: CheckCircle2,
  },
  good_fit: {
    label: "Good Fit",
    color: "text-accent",
    bg: "bg-accent/10",
    border: "border-accent/30",
    icon: TrendingUp,
  },
  partial_fit: {
    label: "Partial Fit",
    color: "text-warning",
    bg: "bg-warning/10",
    border: "border-warning/30",
    icon: AlertTriangle,
  },
  weak_fit: {
    label: "Weak Fit",
    color: "text-danger",
    bg: "bg-danger/10",
    border: "border-danger/30",
    icon: XCircle,
  },
};

export default function FitnessPage() {
  const { session } = useAuth();

  // State
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>("");
  const [resumeText, setResumeText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FitnessScoreResponse | null>(null);
  const [history, setHistory] = useState<FitnessListItem[]>([]);
  const [error, setError] = useState("");
  const [view, setView] = useState<"form" | "result">("form");
  const [pdfFile, setPdfFile] = useState<{ name: string; size: number } | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const extractTextFromPdf = async (file: File) => {
    setPdfLoading(true);
    setError("");
    try {
      const pdfjsLib = await import("pdfjs-dist");
      pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

      const arrayBuffer = await file.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({
        data: new Uint8Array(arrayBuffer),
        useSystemFonts: true,
      });
      const pdf = await loadingTask.promise;
      const pages: string[] = [];

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        const text = content.items
          .map((item) => {
            if ("str" in item) {
              return item.hasEOL ? item.str + "\n" : item.str;
            }
            return "";
          })
          .join("");
        pages.push(text.trim());
      }

      const fullText = pages.filter(Boolean).join("\n\n").trim();
      if (!fullText) {
        setError("Could not extract text from this PDF. It may be image-based — try pasting text instead.");
        return;
      }
      setResumeText(fullText);
      setPdfFile({ name: file.name, size: file.size });
    } catch (e) {
      console.error("PDF parse error:", e);
      setError("Failed to parse PDF. Please try pasting your resume text instead.");
    } finally {
      setPdfLoading(false);
    }
  };

  const handleFileSelect = (file: File | null) => {
    if (!file) return;
    if (file.type !== "application/pdf") {
      setError("Only PDF files are supported.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File too large. Max 10MB.");
      return;
    }
    extractTextFromPdf(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const clearPdf = () => {
    setPdfFile(null);
    setResumeText("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Load analyses & history
  const [dataLoading, setDataLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (!session?.access_token) return;
    setDataLoading(true);

    // Load analyses separately so a fitness table error doesn't block JD list
    try {
      const jdRes = await api.listAnalyses(50, 0);
      setAnalyses(jdRes.analyses.filter((a) => a.status === "completed"));
    } catch (e) {
      console.error("Failed to load JD analyses:", e);
    }

    try {
      const fitRes = await api.listFitnessScores(20, 0);
      setHistory(fitRes.scores);
    } catch {
      // fitness table may not exist yet — that's OK
    }

    setDataLoading(false);
  }, [session]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Submit
  const handleSubmit = async () => {
    if (!selectedAnalysis || !resumeText.trim()) return;
    setLoading(true);
    setError("");
    try {
      api.setToken(session!.access_token);
      const res = await api.scoreFitness({
        analysis_id: selectedAnalysis,
        resume_text: resumeText.trim(),
      });
      setResult(res);
      setView("result");
      loadData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Scoring failed");
    } finally {
      setLoading(false);
    }
  };

  // Score ring SVG helper
  const ScoreRing = ({ score }: { score: number }) => {
    const r = 54;
    const circ = 2 * Math.PI * r;
    const offset = circ - (score / 100) * circ;
    const color =
      score >= 80
        ? "#22c55e"
        : score >= 60
          ? "#c8ff00"
          : score >= 40
            ? "#f59e0b"
            : "#ef4444";
    return (
      <svg width="140" height="140" className="shrink-0">
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke="currentColor"
          className="text-edge"
          strokeWidth="8"
        />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
          className="transition-all duration-1000"
        />
        <text
          x="70"
          y="66"
          textAnchor="middle"
          className="fill-primary font-bold"
          fontSize="32"
        >
          {Math.round(score)}
        </text>
        <text
          x="70"
          y="86"
          textAnchor="middle"
          className="fill-muted"
          fontSize="12"
        >
          / 100
        </text>
      </svg>
    );
  };

  if (view === "result" && result) {
    const vc = verdictConfig[result.verdict] || verdictConfig.partial_fit;
    const VerdictIcon = vc.icon;

    return (
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Back button */}
        <button
          onClick={() => setView("form")}
          className="flex items-center gap-1.5 text-sm text-muted hover:text-primary transition"
        >
          <ArrowLeft className="h-4 w-4" />
          New Assessment
        </button>

        {/* Score hero */}
        <Card className="overflow-hidden">
          <div className="flex flex-col items-center gap-6 p-5 sm:p-8 sm:flex-row sm:items-start sm:gap-10">
            <ScoreRing score={result.fitness_score} />
            <div className="flex-1 text-center sm:text-left">
              <div
                className={cn(
                  "mb-2 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold",
                  vc.bg,
                  vc.border,
                  vc.color,
                  "border"
                )}
              >
                <VerdictIcon className="h-4 w-4" />
                {vc.label}
              </div>
              <p className="text-sm text-secondary leading-relaxed">
                {result.detailed_feedback}
              </p>
              {result.processing_time_ms && (
                <span className="mt-3 inline-flex items-center gap-1 text-xs text-muted font-mono">
                  <Clock className="h-3 w-3" />
                  {(result.processing_time_ms / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          </div>
        </Card>

        {/* Strengths */}
        {result.strengths?.length > 0 && (
          <Card className="animate-reveal d1">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CheckCircle2 className="h-4 w-4 text-ok" />
                Strengths
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2">
                {result.strengths.map((s, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 rounded-lg border border-ok/10 bg-ok/[0.03] px-3.5 py-2.5"
                  >
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-ok/50" />
                    <span className="text-[13px] text-secondary leading-relaxed">
                      {s}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Matched Skills */}
        {result.matched_skills?.length > 0 && (
          <Card className="animate-reveal d2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="h-4 w-4 text-accent" />
                Matched Skills
              </CardTitle>
              <CardDescription>
                Skills from the JD found in your resume
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2">
                {result.matched_skills.map((ms, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-edge/60 bg-surface/40 px-4 py-3"
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-[13px] font-semibold text-primary">
                        {ms.skill}
                      </span>
                      <Badge
                        variant={
                          ms.strength === "strong"
                            ? "accent"
                            : ms.strength === "moderate"
                              ? "warning"
                              : "default"
                        }
                        className="text-[10px]"
                      >
                        {ms.strength}
                      </Badge>
                    </div>
                    <p className="text-[12px] text-muted leading-relaxed">
                      {ms.evidence}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Missing Skills */}
        {result.missing_skills?.length > 0 && (
          <Card className="animate-reveal d3">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <XCircle className="h-4 w-4 text-danger" />
                Missing Skills
              </CardTitle>
              <CardDescription>
                JD requirements not evidenced in your resume
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2">
                {result.missing_skills.map((ms, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-edge/60 bg-surface/40 px-4 py-3"
                  >
                    <div className="mb-1.5 flex items-center justify-between">
                      <span className="text-[13px] font-semibold text-primary">
                        {ms.skill}
                      </span>
                      <Badge
                        variant={
                          ms.importance === "critical"
                            ? "error"
                            : ms.importance === "important"
                              ? "warning"
                              : "default"
                        }
                        className="text-[10px]"
                      >
                        {ms.importance}
                      </Badge>
                    </div>
                    <p className="text-[12px] text-muted leading-relaxed">
                      {ms.suggestion}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Improvements */}
        {result.improvements?.length > 0 && (
          <Card className="animate-reveal d4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="h-4 w-4 text-info" />
                Improvements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {result.improvements.map((imp, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-edge/60 bg-surface/40 p-4"
                  >
                    <div className="mb-1.5 flex items-center justify-between">
                      <span className="text-[13px] font-semibold text-primary">
                        {imp.area}
                      </span>
                      <Badge
                        variant={
                          imp.impact === "high"
                            ? "error"
                            : imp.impact === "medium"
                              ? "warning"
                              : "default"
                        }
                        className="text-[10px]"
                      >
                        {imp.impact} impact
                      </Badge>
                    </div>
                    <p className="mb-1 text-[12px] text-muted">
                      <span className="text-secondary font-medium">Current:</span>{" "}
                      {imp.current_state}
                    </p>
                    <p className="text-[12px] text-accent/80">
                      <span className="font-medium">Action:</span>{" "}
                      {imp.recommended_action}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="animate-reveal">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
          Resume Fitness Scorer
        </h1>
        <p className="mt-1 text-sm text-muted">
          Evaluate how well your resume matches a job description. Select an
          analyzed JD, paste your resume, and get an AI-powered fit assessment.
        </p>
      </div>

      {/* Form */}
      <Card className="animate-reveal d1">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-accent" />
            New Assessment
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* JD Selector — Premium Dropdown */}
          <div className="relative">
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.15em] text-muted/70">
              Select Job Analysis
            </label>
            {(() => {
              const selected = analyses.find((a) => a.id === selectedAnalysis);

              return (
                <div ref={dropdownRef} className="relative">
                  {/* Trigger */}
                  <button
                    type="button"
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className={cn(
                      "group flex w-full items-center justify-between rounded-xl border bg-surface/80 px-4 py-3 text-sm transition-all duration-200",
                      dropdownOpen
                        ? "border-accent/40 shadow-[0_0_20px_rgba(200,255,0,0.06)] ring-1 ring-accent/20"
                        : "border-edge hover:border-edge-strong hover:bg-surface",
                    )}
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className={cn(
                        "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors",
                        selected ? "bg-accent/10" : "bg-edge/50",
                      )}>
                        <Briefcase className={cn("h-3.5 w-3.5", selected ? "text-accent" : "text-muted")} />
                      </div>
                      {selected ? (
                        <div className="min-w-0 text-left">
                          <p className="truncate font-medium text-primary">{selected.role}</p>
                          <p className="truncate text-[11px] text-muted">
                            {selected.company_type}{selected.geography ? ` · ${selected.geography}` : ""}
                          </p>
                        </div>
                      ) : (
                        <span className="text-muted">Choose a completed JD analysis...</span>
                      )}
                    </div>
                    <ChevronDown className={cn(
                      "h-4 w-4 shrink-0 text-muted transition-transform duration-200",
                      dropdownOpen && "rotate-180 text-accent",
                    )} />
                  </button>

                  {/* Dropdown Panel */}
                  {dropdownOpen && (
                    <div className="absolute left-0 right-0 top-full z-50 mt-2 overflow-hidden rounded-xl border border-edge/80 bg-surface/95 shadow-[0_16px_48px_rgba(0,0,0,0.5)] backdrop-blur-2xl">
                      {analyses.length === 0 ? (
                        <div className="px-4 py-6 text-center">
                          {dataLoading ? (
                            <>
                              <Loader2 className="mx-auto mb-2 h-6 w-6 text-accent animate-spin" />
                              <p className="text-xs text-muted">Loading analyses...</p>
                            </>
                          ) : (
                            <>
                              <Briefcase className="mx-auto mb-2 h-8 w-8 text-muted/40" />
                              <p className="text-xs text-muted">No completed analyses found</p>
                              <a href="/dashboard/analyze" className="mt-1 inline-block text-xs text-accent hover:underline">
                                Analyze a JD first →
                              </a>
                            </>
                          )}
                        </div>
                      ) : (
                        <div className="max-h-64 overflow-y-auto py-1.5">
                          {analyses.map((a) => {
                            const isActive = a.id === selectedAnalysis;
                            return (
                              <button
                                key={a.id}
                                type="button"
                                onClick={() => { setSelectedAnalysis(a.id); setDropdownOpen(false); }}
                                className={cn(
                                  "flex w-full items-center gap-3 px-4 py-2.5 text-left transition-all duration-150",
                                  isActive
                                    ? "bg-accent/[0.07]"
                                    : "hover:bg-white/[0.03]",
                                )}
                              >
                                <div className={cn(
                                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg",
                                  isActive ? "bg-accent/15" : "bg-edge/40",
                                )}>
                                  {isActive ? (
                                    <Check className="h-3.5 w-3.5 text-accent" />
                                  ) : (
                                    <Briefcase className="h-3 w-3 text-muted/60" />
                                  )}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className={cn("truncate text-sm", isActive ? "font-semibold text-accent" : "text-primary")}>
                                    {a.role}
                                  </p>
                                  <p className="truncate text-[11px] text-muted">
                                    {a.company_type}{a.geography ? ` · ${a.geography}` : ""}
                                  </p>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })()}
            {!dataLoading && analyses.length === 0 && (
              <p className="mt-1.5 text-xs text-muted">
                No completed analyses found.{" "}
                <a
                  href="/dashboard/analyze"
                  className="text-accent hover:underline"
                >
                  Analyze a JD first
                </a>
                .
              </p>
            )}
          </div>

          {/* Resume — PDF Upload or Paste */}
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.15em] text-muted/70">
              Resume
            </label>

            {/* PDF drop zone */}
            {!resumeText && !pdfLoading && (
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 cursor-pointer transition-all",
                  dragOver
                    ? "border-accent bg-accent/[0.04]"
                    : "border-edge/60 bg-root/40 hover:border-edge-strong hover:bg-surface/30"
                )}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/[0.06]">
                  <Upload className="h-5 w-5 text-accent/60" />
                </div>
                <div className="text-center">
                  <p className="text-[13px] font-medium text-primary">
                    Drop your resume PDF here
                  </p>
                  <p className="mt-0.5 text-[11px] text-muted">
                    or click to browse · PDF up to 10MB
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files?.[0] ?? null)}
                />
              </div>
            )}

            {/* PDF loading state */}
            {pdfLoading && (
              <div className="flex items-center justify-center gap-3 rounded-xl border border-edge/60 bg-root/40 p-8">
                <Loader2 className="h-5 w-5 animate-spin text-accent" />
                <span className="text-[13px] text-secondary">Extracting text from PDF...</span>
              </div>
            )}

            {/* PDF file info badge */}
            {pdfFile && (
              <div className="flex items-center gap-3 rounded-lg border border-accent/15 bg-accent/[0.03] px-3.5 py-2.5 mb-3 mt-2">
                <FileIcon className="h-4 w-4 text-accent shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] font-medium text-primary truncate">{pdfFile.name}</p>
                  <p className="text-[10px] text-muted">{(pdfFile.size / 1024).toFixed(0)} KB · Text extracted</p>
                </div>
                <button onClick={clearPdf} className="rounded p-1 text-muted hover:text-danger transition">
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            {/* Divider */}
            {!resumeText && !pdfLoading && (
              <div className="flex items-center gap-3 my-3">
                <div className="flex-1 h-px bg-edge/50" />
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted/50">or paste text</span>
                <div className="flex-1 h-px bg-edge/50" />
              </div>
            )}

            {/* Textarea (always visible when we have text, or as fallback) */}
            {(resumeText || (!pdfLoading && !pdfFile)) && (
              <>
                <textarea
                  value={resumeText}
                  onChange={(e) => { setResumeText(e.target.value); if (!e.target.value) setPdfFile(null); }}
                  rows={resumeText ? 10 : 4}
                  placeholder="Paste your resume content here..."
                  className="w-full rounded-lg border border-edge bg-surface px-3 py-2.5 text-sm text-primary placeholder:text-muted/40 outline-none transition focus:border-accent/50 focus:ring-1 focus:ring-accent/20 resize-y font-mono text-[13px] leading-relaxed"
                />
                <div className="mt-1.5 flex items-center justify-between">
                  <p className="text-xs text-muted">
                    Include all sections — summary, experience, skills, education.
                  </p>
                  <span className="text-xs text-muted font-mono tabular-nums">
                    {resumeText.length.toLocaleString()} chars
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-lg border border-danger/30 bg-danger-dim px-4 py-3 text-sm text-danger">
              {error}
            </div>
          )}

          {/* Submit */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button
              onClick={handleSubmit}
              disabled={loading || !selectedAnalysis || !resumeText.trim()}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Score My Resume
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* History */}
      {history.length > 0 && (
        <Card className="animate-reveal d2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-4 w-4 text-muted" />
              Recent Assessments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map((item) => {
                const vc =
                  verdictConfig[item.verdict] || verdictConfig.partial_fit;
                return (
                  <button
                    key={item.id}
                    onClick={async () => {
                      try {
                        api.setToken(session!.access_token);
                        const full = await api.getFitness(item.id);
                        setResult(full);
                        setView("result");
                      } catch {
                        /* silent */
                      }
                    }}
                    className="flex w-full items-center justify-between rounded-lg border border-edge/60 bg-surface/40 px-4 py-3 text-left transition hover:border-accent/15 hover:bg-surface/60"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "flex h-9 w-9 items-center justify-center rounded-lg text-sm font-bold",
                          vc.bg,
                          vc.color
                        )}
                      >
                        {Math.round(item.fitness_score)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              item.verdict === "strong_fit"
                                ? "accent"
                                : item.verdict === "good_fit"
                                  ? "warning"
                                  : item.verdict === "partial_fit"
                                    ? "warning"
                                    : "error"
                            }
                            className="text-[10px]"
                          >
                            {vc.label}
                          </Badge>
                        </div>
                        <p className="mt-0.5 text-xs text-muted font-mono">
                          {new Date(item.created_at).toLocaleDateString()}{" "}
                          {item.processing_time_ms &&
                            `· ${(item.processing_time_ms / 1000).toFixed(1)}s`}
                        </p>
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted" />
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
