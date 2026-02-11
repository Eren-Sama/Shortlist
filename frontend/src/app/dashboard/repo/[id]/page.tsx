"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, type RepoAnalysisResponse, type ScoreDimension } from "@/lib/api";
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
  GitBranch,
  Star,
  AlertTriangle,
} from "lucide-react";

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  const pct = (score / 10) * 100;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-secondary">{label}</span>
        <span className="font-mono font-semibold text-primary">{score.toFixed(1)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-edge">
        <div
          className={`h-1.5 rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function DimensionCard({ dimension }: { dimension: ScoreDimension }) {
  const scoreColor =
    dimension.score >= 7
      ? "text-ok"
      : dimension.score >= 5
        ? "text-warn"
        : "text-danger";

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{dimension.name}</CardTitle>
          <span className={`text-2xl font-bold font-mono ${scoreColor}`}>
            {dimension.score.toFixed(1)}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-secondary">{dimension.details}</p>
        {dimension.suggestions.length > 0 && (
          <div>
            <h4 className="mb-1 text-xs font-medium uppercase tracking-wider text-muted">Suggestions</h4>
            <ul className="space-y-1">
              {dimension.suggestions.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-secondary">
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-warn" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function RepoResultsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<RepoAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getRepoAnalysis(id)
      .then(setData)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load")
      )
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-6 w-6 rounded-full border-2 border-accent border-t-transparent animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" /> Back
        </Button>
        <Card>
          <CardContent className="py-8 text-center text-danger">
            {error || "Analysis not found"}
          </CardContent>
        </Card>
      </div>
    );
  }

  const { scorecard } = data;
  const overallColor =
    scorecard.overall_score >= 7
      ? "text-ok"
      : scorecard.overall_score >= 5
        ? "text-warn"
        : "text-danger";

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 sm:gap-4 animate-reveal">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="flex items-center gap-2 text-lg sm:text-2xl font-bold tracking-tight">
            <GitBranch className="h-5 w-5 text-accent" />
            <span className="truncate">{scorecard.repo_name}</span>
          </h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 sm:gap-3 text-sm text-secondary">
            {scorecard.primary_language && (
              <Badge variant="accent">{scorecard.primary_language}</Badge>
            )}
            <span className="font-mono text-xs text-muted">{scorecard.total_files} files</span>
            <span className="font-mono text-xs text-muted">{scorecard.total_lines.toLocaleString()} lines</span>
          </div>
        </div>
      </div>

      {/* Overall Score */}
      <Card className="border-edge-strong animate-reveal d1">
        <CardContent className="py-6 sm:py-8">
          <div className="flex flex-col items-center gap-4 md:flex-row md:gap-8">
            <div className="text-center">
              <div className={`text-4xl sm:text-6xl font-bold font-mono ${overallColor}`}>
                {scorecard.overall_score.toFixed(1)}
              </div>
              <div className="mt-1 text-sm text-muted">/ 10</div>
            </div>
            <div className="flex-1 space-y-3">
              <ScoreBar
                label="Code Quality"
                score={scorecard.code_quality.score}
                color="bg-accent"
              />
              <ScoreBar
                label="Test Coverage"
                score={scorecard.test_coverage.score}
                color="bg-ok"
              />
              <ScoreBar
                label="Complexity"
                score={scorecard.complexity.score}
                color="bg-info"
              />
              <ScoreBar
                label="Structure"
                score={scorecard.structure.score}
                color="bg-warn"
              />
              <ScoreBar
                label="Deploy Ready"
                score={scorecard.deployment_readiness.score}
                color="bg-danger"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      <Card className="animate-reveal d2">
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-secondary leading-relaxed">
            {scorecard.summary}
          </p>
        </CardContent>
      </Card>

      {/* Top Improvements */}
      {scorecard.top_improvements.length > 0 && (
        <Card className="animate-reveal d3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-4 w-4 text-warn" />
              Top Improvements
            </CardTitle>
            <CardDescription>
              Highest impact changes to boost your recruiter score
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-2">
              {scorecard.top_improvements.map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-lg bg-warn-dim text-xs font-bold font-mono text-warn">
                    {i + 1}
                  </span>
                  <span className="text-secondary">{item}</span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {/* Detailed Dimension Cards */}
      <div className="animate-reveal d4">
        <h2 className="mb-4 text-lg font-bold tracking-tight">Detailed Breakdown</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <DimensionCard dimension={scorecard.code_quality} />
          <DimensionCard dimension={scorecard.test_coverage} />
          <DimensionCard dimension={scorecard.complexity} />
          <DimensionCard dimension={scorecard.structure} />
          <DimensionCard dimension={scorecard.deployment_readiness} />
        </div>
      </div>
    </div>
  );
}
