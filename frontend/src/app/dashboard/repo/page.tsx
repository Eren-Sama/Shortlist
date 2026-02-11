"use client";

import { useState, useEffect, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { api, type RepoAnalysisListItem } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { GitBranch, ArrowRight, Github, Clock } from "lucide-react";

function scoreColor(score: number): string {
  if (score >= 8) return "text-ok";
  if (score >= 6) return "text-accent";
  if (score >= 4) return "text-warn";
  return "text-danger";
}

function scoreBg(score: number): string {
  if (score >= 8) return "bg-ok/10 border-ok/20";
  if (score >= 6) return "bg-accent/10 border-accent/20";
  if (score >= 4) return "bg-warn/10 border-warn/20";
  return "bg-danger/10 border-danger/20";
}

export default function RepoAnalyzePage() {
  const router = useRouter();
  const { session } = useAuth();
  const [githubUrl, setGithubUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<RepoAnalysisListItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    if (!session?.access_token) {
      setHistoryLoading(false);
      return;
    }
    api.setToken(session.access_token);
    api
      .listRepoAnalyses(50, 0)
      .then((data) => setHistory(data.analyses))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  }, [session]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await api.analyzeRepo({ github_url: githubUrl });
      router.push(`/dashboard/repo/${result.analysis_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const completedHistory = history.filter((a) => a.status === "completed");
  const pendingHistory = history.filter(
    (a) => a.status === "pending" || a.status === "processing"
  );

  return (
    <div className="mx-auto max-w-2xl space-y-6 sm:space-y-8">
      <div className="animate-reveal">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">Analyze Repository</h1>
        <p className="mt-1 text-[13px] sm:text-sm text-secondary leading-relaxed">
          Paste a public GitHub repository URL and our AI will generate a
          recruiter-focused scorecard.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card className="animate-reveal d1">
          <CardHeader>
            <CardTitle className="text-base sm:text-lg">GitHub Repository URL</CardTitle>
            <CardDescription className="text-[12px] sm:text-sm break-all">
              Must be a public repository: https://github.com/owner/repo
            </CardDescription>
          </CardHeader>
          <CardContent>
            <input
              type="url"
              required
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              pattern="https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+/?"
              title="Must be a valid GitHub URL: https://github.com/owner/repo"
              className="w-full rounded-lg px-4 py-3 text-sm"
            />
          </CardContent>
        </Card>

        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger-dim px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        <Button type="submit" size="lg" loading={loading} className="w-full">
          <GitBranch className="h-4 w-4" />
          {loading ? "Analyzing Repository..." : "Analyze Repository"}
        </Button>
      </form>

      <Card className="animate-reveal d2">
        <CardContent className="py-6">
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
            What gets analyzed
          </h3>
          <ul className="space-y-2 text-sm text-secondary">
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-accent">{"\u2022"}</span>
              <span>
                <strong className="text-primary">Code Quality</strong> {"\u2014"} Readability, naming, error handling, patterns
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-ok">{"\u2022"}</span>
              <span>
                <strong className="text-primary">Test Coverage</strong> {"\u2014"} Presence and quality of tests
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-info">{"\u2022"}</span>
              <span>
                <strong className="text-primary">Complexity</strong> {"\u2014"} Architecture decisions, non-trivial logic
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-warn">{"\u2022"}</span>
              <span>
                <strong className="text-primary">Structure</strong> {"\u2014"} Organization, README, documentation
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-danger">{"\u2022"}</span>
              <span>
                <strong className="text-primary">Deployment Readiness</strong> {"\u2014"} Docker, CI/CD, configs
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>

      <div className="animate-reveal d3 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold tracking-tight">Past Analyses</h2>
          {completedHistory.length > 0 && (
            <span className="text-xs text-muted">
              {completedHistory.length} completed
            </span>
          )}
        </div>

        {historyLoading ? (
          <div className="flex justify-center py-10">
            <div className="h-5 w-5 rounded-full border-2 border-accent border-t-transparent animate-spin" />
          </div>
        ) : history.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center">
              <Github className="mx-auto mb-3 h-10 w-10 text-muted" />
              <h3 className="mb-1 font-semibold text-primary">
                No analyses yet
              </h3>
              <p className="text-sm text-secondary">
                Analyze a repo above to see your history here
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="flex flex-col gap-4">
            {/* pending / processing items */}
            {pendingHistory.map((a, i) => (
              <Card
                key={a.id}
                className={`animate-reveal d${Math.min(i + 4, 8)} border-edge/40`}
              >
                <CardContent className="flex items-center justify-between py-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-warn animate-pulse" />
                      <span className="truncate text-sm font-medium text-primary">
                        {a.repo_name || a.github_url.replace("https://github.com/", "")}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-muted">
                      {a.status === "pending" ? "Queued" : "Processing"}
                      {" \u2014 "}
                      {new Date(a.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge className="shrink-0 capitalize">
                    {a.status}
                  </Badge>
                </CardContent>
              </Card>
            ))}

            {/* completed items */}
            {completedHistory.map((a, i) => (
              <Link key={a.id} href={`/dashboard/repo/${a.id}`}>
                <Card
                  className={`group cursor-pointer transition hover:border-edge-strong animate-reveal d${Math.min(i + 4, 8)}`}
                >
                  <CardContent className="flex items-center gap-3 sm:gap-4 py-4">
                    {/* score circle */}
                    <div
                      className={`flex h-10 w-10 sm:h-11 sm:w-11 shrink-0 items-center justify-center rounded-full border ${scoreBg(a.overall_score ?? 0)}`}
                    >
                      <span
                        className={`text-xs sm:text-sm font-bold ${scoreColor(a.overall_score ?? 0)}`}
                      >
                        {(a.overall_score ?? 0).toFixed(1)}
                      </span>
                    </div>

                    {/* info */}
                    <div className="min-w-0 flex-1">
                      <h3 className="truncate text-xs sm:text-sm font-semibold text-primary">
                        {a.repo_name || a.github_url.replace("https://github.com/", "")}
                      </h3>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        {a.primary_language && (
                          <Badge className="text-[10px]">
                            {a.primary_language}
                          </Badge>
                        )}
                        <span className="flex items-center gap-1 text-[11px] text-muted">
                          <Clock className="h-3 w-3" />
                          {new Date(a.created_at).toLocaleDateString()}
                        </span>
                        {a.processing_time_ms && (
                          <span className="text-[11px] text-muted">
                            {(a.processing_time_ms / 1000).toFixed(1)}s
                          </span>
                        )}
                      </div>
                    </div>

                    {/* arrow */}
                    <ArrowRight className="h-4 w-4 shrink-0 text-muted transition group-hover:text-accent" />
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
